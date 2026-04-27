function confirmAge() {
    localStorage.setItem("packageStoreAgeConfirmed", "yes");
    document.getElementById("ageModal").style.display = "none";
}

window.addEventListener("load", function () {
    const confirmed = localStorage.getItem("packageStoreAgeConfirmed");
    if (!confirmed) {
        document.getElementById("ageModal").style.display = "grid";
    }
});