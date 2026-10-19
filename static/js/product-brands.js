for (const logo of document.querySelectorAll(".product-brand-logo")) {
  logo.addEventListener("error", () => {
    logo.classList.add("product-brand-logo-unavailable");
  });
}
