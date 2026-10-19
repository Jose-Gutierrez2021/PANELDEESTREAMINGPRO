const productOptions = document.querySelectorAll(
  'input[name="product_id"][data-price]',
);
const totalLabel = document.querySelector("#sale-total");

if (productOptions.length && totalLabel) {
  const copFormatter = new Intl.NumberFormat("es-CO", {
    maximumFractionDigits: 0,
  });

  const updateTotal = (event) => {
    const rawPrice = event?.target?.dataset.price;
    const price = rawPrice ? Number(rawPrice) : Number.NaN;

    if (Number.isFinite(price)) {
      totalLabel.textContent = `$${copFormatter.format(price)}`;
    } else {
      totalLabel.textContent = "Selecciona un producto";
    }
  };

  for (const option of productOptions) {
    option.addEventListener("change", updateTotal);
  }
}
