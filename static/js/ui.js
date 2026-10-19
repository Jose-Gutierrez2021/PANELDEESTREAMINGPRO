document.addEventListener("DOMContentLoaded", () => {
  const loadingScreen = document.getElementById("loading-screen");
  const loadingMessage = loadingScreen?.querySelector(".loading-message");

  document.querySelectorAll("form[data-loading-message]").forEach((form) => {
    form.addEventListener("submit", () => {
      if (!loadingScreen || !loadingMessage) {
        return;
      }

      loadingMessage.textContent = form.dataset.loadingMessage;
      loadingScreen.classList.add("is-active");
      loadingScreen.setAttribute("aria-hidden", "false");

      form.querySelectorAll('button[type="submit"], button:not([type])').forEach((button) => {
        button.disabled = true;
      });
    });
  });

  document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const password = document.getElementById(button.dataset.passwordToggle);
      if (!password) {
        return;
      }

      const showPassword = password.type === "password";
      password.type = showPassword ? "text" : "password";
      button.setAttribute("aria-pressed", String(showPassword));
      button.setAttribute(
        "aria-label",
        showPassword ? "Ocultar contraseña" : "Mostrar contraseña"
      );
    });
  });

  document.querySelectorAll("[data-music-widget]").forEach((widget) => {
    const audio = widget.querySelector("[data-music-audio]");
    const playPauseButton = widget.querySelector("[data-music-play-pause]");
    const previousButton = widget.querySelector("[data-music-previous]");
    const nextButton = widget.querySelector("[data-music-next]");
    const progress = widget.querySelector("[data-music-progress]");
    const currentTime = widget.querySelector("[data-music-current-time]");
    const duration = widget.querySelector("[data-music-duration]");
    const volume = widget.querySelector("[data-music-volume]");
    const bass = widget.querySelector("[data-music-bass]");
    const bassValue = widget.querySelector("[data-music-bass-value]");
    const title = widget.querySelector("[data-music-title]");
    const artist = widget.querySelector("[data-music-artist]");
    const playlistElement = widget.querySelector("[data-music-playlist]");
    const status = widget.querySelector("[data-music-status]");

    if (
      !audio || !playPauseButton || !previousButton || !nextButton || !progress ||
      !currentTime || !duration || !volume || !bass || !bassValue || !title || !artist ||
      !playlistElement || !status
    ) {
      return;
    }

    let playlist;
    try {
      playlist = JSON.parse(playlistElement.textContent);
    } catch (error) {
      console.error("No se pudo leer la lista de música del reproductor.", error);
      status.textContent = "No se pudo cargar la lista de música.";
      playPauseButton.disabled = true;
      return;
    }

    if (!Array.isArray(playlist) || playlist.length === 0) {
      title.textContent = "Sin canciones";
      artist.textContent = "Añade audio a static/music";
      status.textContent = "No hay canciones asignadas al servidor.";
      playPauseButton.disabled = true;
      return;
    }

    const playbackStateKey = "streampanel-music-playback";
    const bassLevelKey = "streampanel-music-bass";
    let currentTrackIndex = 0;
    let shouldResumePlayback = false;
    let pendingStartTime = 0;
    let playbackRequestId = 0;
    let audioContext = null;
    let bassFilter = null;
    let bassCompressor = null;

    try {
      const savedState = JSON.parse(window.localStorage.getItem(playbackStateKey) || "null");
      if (savedState && typeof savedState === "object") {
        const matchingTrackIndex = playlist.findIndex((track) => track.src === savedState.src);
        currentTrackIndex = matchingTrackIndex >= 0
          ? matchingTrackIndex
          : Number.isInteger(savedState.trackIndex) &&
              savedState.trackIndex >= 0 &&
              savedState.trackIndex < playlist.length
            ? savedState.trackIndex
            : 0;
        pendingStartTime = Number.isFinite(savedState.currentTime) && savedState.currentTime > 0
          ? savedState.currentTime
          : 0;
        shouldResumePlayback = typeof savedState.shouldResumePlayback === "boolean"
          ? savedState.shouldResumePlayback
          : false;
      }
    } catch (error) {
      console.warn("No se pudo restaurar el estado del reproductor.", error);
    }

    const savePlaybackState = () => {
      const track = playlist[currentTrackIndex];
      if (!track) {
        return;
      }
      try {
        window.localStorage.setItem(playbackStateKey, JSON.stringify({
          src: track.src,
          trackIndex: currentTrackIndex,
          currentTime: audio.readyState >= 1 && Number.isFinite(audio.currentTime)
            ? audio.currentTime
            : pendingStartTime,
          shouldResumePlayback,
        }));
      } catch (error) {
        console.warn("No se pudo guardar el estado del reproductor.", error);
      }
    };

    const formatTime = (time) => {
      if (!Number.isFinite(time)) {
        return "0:00";
      }
      const minutes = Math.floor(time / 60);
      const seconds = Math.floor(time % 60).toString().padStart(2, "0");
      return `${minutes}:${seconds}`;
    };

    const updatePlayButton = () => {
      const isPlaying = !audio.paused;
      playPauseButton.dataset.playbackState = isPlaying ? "playing" : "paused";
      playPauseButton.setAttribute("aria-label", isPlaying ? "Pausar" : "Reproducir");
      playPauseButton.title = isPlaying ? "Pausar" : "Reproducir";
    };

    const updateVolumeTrack = () => {
      volume.style.setProperty("--volume", `${Number(volume.value) * 100}%`);
    };

    const updateBassTrack = () => {
      const maxBass = Number(bass.max || 12);
      const bassLevel = Number(bass.value);
      bass.style.setProperty("--bass", `${(bassLevel / maxBass) * 100}%`);
      bassValue.textContent = `+${bassLevel} dB`;
      if (bassFilter) {
        const filteredGain = bassLevel * 0.7;
        bassFilter.gain.setTargetAtTime(
          filteredGain,
          audioContext.currentTime,
          0.12,
        );
      }
    };

    const activateBassFilter = async () => {
      const AudioContextConstructor = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextConstructor) {
        status.textContent = "Tu navegador no admite el realce de bajos.";
        return false;
      }

      try {
        if (!audioContext) {
          audioContext = new AudioContextConstructor();
          bassFilter = audioContext.createBiquadFilter();
          bassFilter.type = "lowshelf";
          bassFilter.frequency.value = 90;
          bassFilter.Q.value = 0.8;
          bassFilter.gain.value = Number(bass.value) * 0.7;
          bassCompressor = audioContext.createDynamicsCompressor();
          bassCompressor.threshold.value = -8;
          bassCompressor.knee.value = 8;
          bassCompressor.ratio.value = 4;
          bassCompressor.attack.value = 0.003;
          bassCompressor.release.value = 0.2;
          audioContext.createMediaElementSource(audio).connect(bassFilter);
          bassFilter.connect(bassCompressor);
          bassCompressor.connect(audioContext.destination);
        }
        if (audioContext.state === "suspended") {
          await audioContext.resume();
        }
        updateBassTrack();
        status.textContent = "";
        return true;
      } catch (error) {
        console.error("No se pudo activar el ecualizador de bajos.", error);
        status.textContent = "No se pudo activar el ecualizador de bajos.";
        return false;
      }
    };

    const loadTrack = async (index, autoplay, startAt = 0) => {
      const track = playlist[index];
      if (!track || typeof track.src !== "string") {
        status.textContent = "No se pudo cargar una canción de la lista.";
        return;
      }

      const requestId = ++playbackRequestId;
      currentTrackIndex = index;
      pendingStartTime = startAt;
      shouldResumePlayback = autoplay;
      title.textContent = track.title || "Canción";
      artist.textContent = track.artist || "Audio local";
      currentTime.textContent = "0:00";
      duration.textContent = "0:00";
      progress.value = "0";
      progress.max = "0";
      progress.style.setProperty("--played", "0%");
      audio.src = track.src;
      audio.load();
      updatePlayButton();
      savePlaybackState();

      if (autoplay) {
        try {
          await audio.play();
          if (requestId !== playbackRequestId || !shouldResumePlayback) {
            return;
          }
          status.textContent = "";
        } catch (error) {
          if (requestId !== playbackRequestId || !shouldResumePlayback) {
            return;
          }
          shouldResumePlayback = false;
          savePlaybackState();
          status.textContent = "Pulsa reproducir para iniciar la canción.";
          updatePlayButton();
        }
      }
    };

    const storedVolume = window.localStorage.getItem("streampanel-music-volume");
    const savedVolume = storedVolume === null ? Number.NaN : Number(storedVolume);
    audio.volume = Number.isFinite(savedVolume) && savedVolume >= 0 && savedVolume <= 1
      ? savedVolume
      : 0.65;
    volume.value = String(audio.volume);
    updateVolumeTrack();

    const storedBass = window.localStorage.getItem(bassLevelKey);
    const savedBass = storedBass === null ? 4 : Number(storedBass);
    bass.value = String(Number.isFinite(savedBass) && savedBass >= 0 && savedBass <= Number(bass.max || 12)
      ? savedBass
      : 4);
    updateBassTrack();

    audio.addEventListener("loadedmetadata", () => {
      duration.textContent = formatTime(audio.duration);
      progress.max = String(audio.duration || 0);
      if (pendingStartTime > 0) {
        audio.currentTime = Math.min(pendingStartTime, Math.max(0, audio.duration - 0.1));
        pendingStartTime = 0;
      }
      currentTime.textContent = formatTime(audio.currentTime);
      progress.value = String(audio.currentTime);
      const percent = audio.duration ? (audio.currentTime / audio.duration) * 100 : 0;
      progress.style.setProperty("--played", `${percent}%`);
      savePlaybackState();
    });

    audio.addEventListener("timeupdate", () => {
      currentTime.textContent = formatTime(audio.currentTime);
      progress.value = String(audio.currentTime);
      const percent = audio.duration ? (audio.currentTime / audio.duration) * 100 : 0;
      progress.style.setProperty("--played", `${percent}%`);
      savePlaybackState();
    });

    audio.addEventListener("play", () => {
      updatePlayButton();
      savePlaybackState();
    });
    audio.addEventListener("pause", () => {
      updatePlayButton();
      savePlaybackState();
    });
    audio.addEventListener("ended", () => {
      const nextIndex = (currentTrackIndex + 1) % playlist.length;
      void loadTrack(nextIndex, true);
    });
    audio.addEventListener("error", () => {
      const track = playlist[currentTrackIndex];
      status.textContent = `No se pudo cargar ${track?.title || "la canción"}.`;
    });

    playPauseButton.addEventListener("click", async () => {
      if (shouldResumePlayback) {
        playbackRequestId += 1;
        shouldResumePlayback = false;
        audio.pause();
        savePlaybackState();
      } else {
        const requestId = ++playbackRequestId;
        shouldResumePlayback = true;
        savePlaybackState();
        try {
          await activateBassFilter();
          if (requestId !== playbackRequestId || !shouldResumePlayback) {
            return;
          }
          await audio.play();
          if (requestId !== playbackRequestId || !shouldResumePlayback) {
            return;
          }
          if (audioContext?.state === "running") {
            status.textContent = "";
          }
        } catch (error) {
          if (requestId !== playbackRequestId || !shouldResumePlayback) {
            return;
          }
          shouldResumePlayback = false;
          savePlaybackState();
          status.textContent = "El navegador no pudo reproducir el audio. Intenta de nuevo.";
        }
      }
    });

    const changeTrack = (direction) => {
      const nextIndex = (currentTrackIndex + direction + playlist.length) % playlist.length;
      void loadTrack(nextIndex, true);
    };

    previousButton.addEventListener("click", () => changeTrack(-1));
    nextButton.addEventListener("click", () => changeTrack(1));

    const musicInputs = [progress, volume, bass];
    musicInputs.forEach((input) => {
      input.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
          event.preventDefault();
          event.stopPropagation();
        }
      });
    });

    progress.addEventListener("input", () => {
      audio.currentTime = Number(progress.value);
      savePlaybackState();
    });

    volume.addEventListener("input", () => {
      audio.volume = Number(volume.value);
      updateVolumeTrack();
      window.localStorage.setItem("streampanel-music-volume", volume.value);
    });

    bass.addEventListener("input", async () => {
      updateBassTrack();
      window.localStorage.setItem(bassLevelKey, bass.value);
      await activateBassFilter();
    });

    window.addEventListener("pagehide", savePlaybackState);
    updatePlayButton();
    loadTrack(currentTrackIndex, shouldResumePlayback, pendingStartTime);
  });
});
