document.addEventListener('DOMContentLoaded', () => {
  const navbarBurger = document.getElementById('navbarBurger');
  const navbarMenu = document.getElementById('navbarMenu');
  navbarBurger.addEventListener('click', () => {
    navbarBurger.classList.toggle('is-active');
    navbarMenu.classList.toggle('is-active');
  });
});
