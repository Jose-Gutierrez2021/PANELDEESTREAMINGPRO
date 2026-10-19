const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const { performance } = require("node:perf_hooks");

const root = __dirname;
const baseUrl = new URL(process.env.MONITOR_URL || "http://127.0.0.1:5000/");
const intervalMs = Number(process.env.MONITOR_INTERVAL_MS || 5000);
const backupIntervalMs = Number(process.env.BACKUP_INTERVAL_MS || 2 * 60 * 60 * 1000);
const latencyLimitMs = 500;
const requestTimeoutMs = 3000;
const backupRoot = path.join(path.dirname(root), `${path.basename(root)}-backup`);
const backupPath = path.join(backupRoot, "latest");
const backupStagingPath = path.join(backupRoot, "latest.tmp");
const backupPreviousPath = path.join(backupRoot, "latest.previous");
const ignoredDirectories = new Set([
  ".git",
  ".venv",
  ".venv-1",
  "__pycache__",
  "instance",
  "node_modules",
]);

let serverProcess = null;
let shuttingDown = false;
let restartingServer = false;
let pollTimer = null;
let backupTimer = null;
let watchHandle = null;
let backupInProgress = false;
const pendingFileChanges = new Map();

function timestamp() {
  return new Date().toLocaleTimeString("es-MX", { hour12: false });
}

function errorMessage(error) {
  return error instanceof Error ? error.message : String(error);
}

function print(message, color = "\u001b[36m") {
  const reset = process.stdout.isTTY ? "\u001b[0m" : "";
  const prefix = process.stdout.isTTY ? color : "";
  console.log(`${prefix}[${timestamp()}] ${message}${reset}`);
}

async function pathExists(target) {
  try {
    await fs.promises.lstat(target);
    return true;
  } catch (error) {
    if (error.code === "ENOENT") {
      return false;
    }
    throw error;
  }
}

async function recoverBackupState() {
  await fs.promises.mkdir(backupRoot, { recursive: true });

  if (await pathExists(backupPath)) {
    await fs.promises.rm(backupPreviousPath, { recursive: true, force: true });
  } else if (await pathExists(backupPreviousPath)) {
    await fs.promises.rename(backupPreviousPath, backupPath);
    print("Se recuperó la última copia válida tras una interrupción.", "\u001b[33m");
  }

  await fs.promises.rm(backupStagingPath, { recursive: true, force: true });
}

async function runBackup(reason) {
  if (backupInProgress || shuttingDown) {
    return;
  }

  backupInProgress = true;
  print(`Iniciando copia completa (${reason}) en ${backupPath}.`, "\u001b[36m");

  try {
    await recoverBackupState();
    await fs.promises.cp(root, backupStagingPath, {
      recursive: true,
      dereference: false,
      preserveTimestamps: true,
      verbatimSymlinks: true,
    });

    let replacedPrevious = false;
    if (await pathExists(backupPath)) {
      await fs.promises.rename(backupPath, backupPreviousPath);
      replacedPrevious = true;
    }

    try {
      await fs.promises.rename(backupStagingPath, backupPath);
    } catch (error) {
      if (replacedPrevious) {
        await fs.promises.rename(backupPreviousPath, backupPath);
      }
      throw error;
    }

    if (replacedPrevious) {
      try {
        await fs.promises.rm(backupPreviousPath, { recursive: true, force: true });
      } catch (error) {
        print(`La copia nueva está lista, pero no se pudo retirar la anterior: ${errorMessage(error)}`, "\u001b[31m");
        backupInProgress = false;
        return;
      }
    }

    print(`COPIA COMPLETA GUARDADA. La copia anterior fue reemplazada; solo queda la más reciente.`, "\u001b[32m");
  } catch (error) {
    print(`ERROR al crear la copia; se conserva la copia anterior: ${errorMessage(error)}`, "\u001b[31m");
    try {
      await fs.promises.rm(backupStagingPath, { recursive: true, force: true });
    } catch (cleanupError) {
      print(`No se pudo retirar la carpeta temporal ${backupStagingPath}: ${errorMessage(cleanupError)}`, "\u001b[31m");
    }
  } finally {
    backupInProgress = false;
  }
}

function latencyLabel(result) {
  if (!result.ok) {
    return `ERROR (${result.error})`;
  }

  const state = result.latencyMs <= latencyLimitMs ? "OK" : "LENTO";
  return `HTTP ${result.status} ${result.latencyMs} ms ${state}`;
}

async function checkEndpoint(endpoint) {
  const url = new URL(endpoint, baseUrl.origin);
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), requestTimeoutMs);
  const startedAt = performance.now();

  try {
    const response = await fetch(url, {
      signal: controller.signal,
      redirect: "follow",
    });

    return {
      ok: response.ok,
      status: response.status,
      latencyMs: Math.round(performance.now() - startedAt),
    };
  } catch (error) {
    return {
      ok: false,
      error: error.name === "AbortError" ? "tiempo agotado" : error.message,
    };
  } finally {
    clearTimeout(timeout);
  }
}

function findPython() {
  if (process.env.PYTHON) {
    return process.env.PYTHON;
  }

  for (const relativePath of [
    ".venv-1/Scripts/python.exe",
    ".venv/Scripts/python.exe",
    ".venv-1/bin/python",
    ".venv/bin/python",
  ]) {
    const candidate = path.join(root, relativePath);
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }

  return process.platform === "win32" ? "py" : "python3";
}

function startFlask() {
  const python = findPython();
  const port = Number(baseUrl.port || 5000);
  print(`Iniciando Flask sin recargador interno en el puerto ${port} con ${python}.`, "\u001b[33m");
  serverProcess = spawn(python, [
    "-u",
    "-c",
    `from app import app; app.run(host="0.0.0.0", port=${port}, debug=False)`,
  ], {
    cwd: root,
    env: { ...process.env, PYTHONUNBUFFERED: "1" },
    stdio: "inherit",
    windowsHide: true,
  });

  serverProcess.on("error", (error) => {
    print(`No se pudo iniciar Flask: ${error.message}`, "\u001b[31m");
  });

  serverProcess.on("exit", (code, signal) => {
    if (restartingServer) {
      restartingServer = false;
      if (!shuttingDown) {
        setTimeout(startFlask, 250);
      }
      return;
    }
    if (!shuttingDown) {
      print(`Flask terminó (código ${code ?? "n/a"}, señal ${signal ?? "n/a"}).`, "\u001b[31m");
    }
  });
}

function restartFlask() {
  if (!serverProcess || serverProcess.exitCode !== null || restartingServer) {
    return;
  }

  restartingServer = true;
  print("Reiniciando el Flask iniciado por Node para aplicar el cambio Python.", "\u001b[33m");
  serverProcess.kill();
}

function ignored(relativePath) {
  const parts = relativePath.split(/[\\/]/);
  return parts.some((part) => ignoredDirectories.has(part) || part === ".env");
}

function watchForChanges() {
  watchHandle = fs.watch(root, { recursive: true }, (eventType, filename) => {
    if (!filename) {
      return;
    }

    const relativePath = String(filename).replace(/\\/g, "/");
    if (ignored(relativePath)) {
      return;
    }

    const extension = path.extname(relativePath).toLowerCase();
    if (![".css", ".html", ".js", ".json", ".md", ".py"].includes(extension)) {
      return;
    }

    const absolutePath = path.join(root, relativePath);
    const changeType = fs.existsSync(absolutePath)
      ? eventType === "rename" ? "CREADO/RENOMBRADO" : "MODIFICADO"
      : "ELIMINADO";

    clearTimeout(pendingFileChanges.get(relativePath));
    const timer = setTimeout(() => {
      pendingFileChanges.delete(relativePath);
      print(`ARCHIVO ${changeType}: ${relativePath}`, "\u001b[35m");
      if (extension === ".py") {
        if (serverProcess) {
          restartFlask();
        } else {
          print("Conectado a un Flask externo; su configuración de recarga controla el reinicio Python.", "\u001b[33m");
        }
      }
    }, 120);
    pendingFileChanges.set(relativePath, timer);
  });

  watchHandle.on("error", (error) => {
    print(`Error vigilando cambios de archivos: ${error.message}`, "\u001b[31m");
  });
}

async function pollLatency() {
  if (shuttingDown) {
    return;
  }

  const [health, login] = await Promise.all([
    checkEndpoint("/health"),
    checkEndpoint("/login"),
  ]);
  const healthColor = health.ok && health.latencyMs <= latencyLimitMs
    ? "\u001b[32m"
    : "\u001b[31m";
  const loginColor = login.ok && login.latencyMs <= latencyLimitMs
    ? "\u001b[32m"
    : "\u001b[31m";

  print(`LATENCIA /health: ${latencyLabel(health)} | /login: ${latencyLabel(login)} (límite ${latencyLimitMs} ms)`, healthColor);
  if (healthColor !== loginColor) {
    print(`Estado de /login: ${latencyLabel(login)}`, loginColor);
  }

  pollTimer = setTimeout(pollLatency, intervalMs);
}

async function waitForFlask() {
  const deadline = Date.now() + 30000;
  while (!shuttingDown && Date.now() < deadline) {
    const health = await checkEndpoint("/health");
    if (health.ok) {
      print(`Flask disponible en ${baseUrl.origin}; comprobación inicial: ${latencyLabel(health)}.`, "\u001b[32m");
      return true;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  print(`Flask no estuvo disponible en 30 segundos: ${baseUrl.origin}/health`, "\u001b[31m");
  return false;
}

function shutdown() {
  if (shuttingDown) {
    return;
  }

  shuttingDown = true;
  clearTimeout(pollTimer);
  clearInterval(backupTimer);
  for (const timer of pendingFileChanges.values()) {
    clearTimeout(timer);
  }
  watchHandle?.close();

  if (serverProcess && serverProcess.exitCode === null) {
    print("Deteniendo el servidor Flask iniciado por este monitor.", "\u001b[33m");
    serverProcess.kill();
  }

  print("Monitor Node detenido.");
}

async function main() {
  if (!["http:", "https:"].includes(baseUrl.protocol)) {
    throw new Error("MONITOR_URL debe comenzar con http:// o https://.");
  }
  if (!Number.isFinite(intervalMs) || intervalMs < 1000) {
    throw new Error("MONITOR_INTERVAL_MS debe ser un número de al menos 1000.");
  }
  if (!Number.isFinite(backupIntervalMs) || backupIntervalMs < 1000) {
    throw new Error("BACKUP_INTERVAL_MS debe ser un número de al menos 1000.");
  }

  print(`Monitor Node activo para ${baseUrl.origin}. Ctrl+C para detenerlo.`);
  print(`Revisando /health y /login cada ${intervalMs} ms; objetivo de latencia: <= ${latencyLimitMs} ms.`);
  print(`Copia completa inicial y luego cada ${backupIntervalMs / 3600000} h; se conserva solo la última.`);
  print("La copia incluye todos los archivos del proyecto, también .env, .git, entornos y la base de datos local.", "\u001b[33m");
  watchForChanges();
  void runBackup("inicio del monitor");
  backupTimer = setInterval(() => {
    void runBackup("intervalo programado");
  }, backupIntervalMs);

  const initialHealth = await checkEndpoint("/health");
  if (!initialHealth.ok) {
    startFlask();
    if (!(await waitForFlask())) {
      process.exitCode = 1;
      shutdown();
      return;
    }
  } else {
    print(`Conectado al Flask existente: ${latencyLabel(initialHealth)}.`, "\u001b[32m");
  }

  await pollLatency();
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
process.on("uncaughtException", (error) => {
  print(`Error inesperado: ${error.stack || error.message}`, "\u001b[31m");
  shutdown();
  process.exitCode = 1;
});

main().catch((error) => {
  print(`No se pudo iniciar el monitor: ${error.message}`, "\u001b[31m");
  shutdown();
  process.exitCode = 1;
});
