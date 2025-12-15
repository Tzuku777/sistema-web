// plataforma/static/plataforma/js/solicitud_rol.js

document.addEventListener("DOMContentLoaded", function () {
  // Selector más robusto: por name, no solo por id
  const tipoSelect =
    document.getElementById("id_tipo_solicitud") ||
    document.querySelector('[name="tipo_solicitud"]');

  const bloqueLenia = document.getElementById("bloque-lenia");
  const bloqueServicios = document.getElementById("bloque-servicios");

  if (!tipoSelect || !bloqueLenia || !bloqueServicios) {
    return; // Si algo falta, no hacemos nada
  }

  function actualizarBloques() {
    let val = (tipoSelect.value || "").toUpperCase();

    // Valores esperados según tu modelo:
    // PROVEEDOR / PRESTADOR / AMBOS 
    if (val === "PROVEEDOR") {
      bloqueLenia.style.display = "block";
      bloqueServicios.style.display = "none";
    } else if (val === "PRESTADOR") {
      bloqueLenia.style.display = "none";
      bloqueServicios.style.display = "block";
    } else if (val === "AMBOS") {
      bloqueLenia.style.display = "block";
      bloqueServicios.style.display = "block";
    } else {
      // Consumidor / sin selección → nada comercial
      bloqueLenia.style.display = "none";
      bloqueServicios.style.display = "none";
    }
  }

  tipoSelect.addEventListener("change", actualizarBloques);
  actualizarBloques(); // Estado inicial (edición / registro ya con valor)
});
