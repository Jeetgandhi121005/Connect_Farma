window.addEventListener("DOMContentLoaded", () => {
  const loader = document.getElementById("loader");

  if (sessionStorage.getItem("loaderShown") === "true") {
    loader.style.display = "none";
  } else {
    setTimeout(() => {
      loader.style.display = "none";
      sessionStorage.setItem("loaderShown", "true");
    }, 1500); // 1.5s loader
  }
});
