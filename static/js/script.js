function confirmAge() {
    localStorage.setItem("packageStoreAgeConfirmed", "yes");
    document.getElementById("ageModal").style.display = "none";
}

function formatMoney(value) {
    return "$" + Number(value).toFixed(2);
}

function updateCheckoutSummary() {
    const subtotalElement = document.getElementById("summarySubtotal");
    const taxElement = document.getElementById("summaryTax");
    const deliveryElement = document.getElementById("summaryDelivery");
    const totalElement = document.getElementById("summaryTotal");

    if (!subtotalElement || !taxElement || !deliveryElement || !totalElement) {
        return;
    }

    const selectedDelivery = document.querySelector("input[name='delivery_method']:checked");
    const subtotal = Number(subtotalElement.dataset.subtotal || 0);
    const taxRate = Number(taxElement.dataset.taxRate || 0);
    const deliveryFee = selectedDelivery ? Number(selectedDelivery.dataset.fee || 0) : 0;
    const tax = subtotal * taxRate;
    const total = subtotal + tax + deliveryFee;

    taxElement.textContent = formatMoney(tax);
    deliveryElement.textContent = formatMoney(deliveryFee);
    totalElement.textContent = formatMoney(total);
}

function toggleDeliveryFields() {
    const selectedDelivery = document.querySelector("input[name='delivery_method']:checked");
    const addressBox = document.getElementById("addressFields");
    const addressInputs = document.querySelectorAll(".delivery-address");
    const isDelivery = selectedDelivery && selectedDelivery.value !== "pickup";

    if (addressBox) {
        addressBox.classList.toggle("is-muted", !isDelivery);
    }
    addressInputs.forEach((input) => {
        input.required = Boolean(isDelivery);
    });
}

function toggleCardFields() {
    const selectedPayment = document.querySelector("input[name='payment_method']:checked");
    const cardBox = document.getElementById("cardFields");
    const cardInputs = document.querySelectorAll(".card-input");
    const isCard = selectedPayment && selectedPayment.value === "card";

    if (cardBox) {
        cardBox.classList.toggle("is-muted", !isCard);
    }
    cardInputs.forEach((input) => {
        input.required = Boolean(isCard);
    });
}

window.addEventListener("load", function () {
    const confirmed = localStorage.getItem("packageStoreAgeConfirmed");
    if (!confirmed) {
        document.getElementById("ageModal").style.display = "grid";
    }

    document.querySelectorAll("input[name='delivery_method']").forEach((input) => {
        input.addEventListener("change", function () {
            updateCheckoutSummary();
            toggleDeliveryFields();
        });
    });

    document.querySelectorAll("input[name='payment_method']").forEach((input) => {
        input.addEventListener("change", toggleCardFields);
    });

    updateCheckoutSummary();
    toggleDeliveryFields();
    toggleCardFields();
});
