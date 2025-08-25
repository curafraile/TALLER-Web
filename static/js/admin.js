// Este es el código de tu archivo js/admin.js
const semanas = {};
document.querySelectorAll('.fecha-lunes').forEach(el => {
    const curso_id = el.id.split('_')[2];
    semanas[curso_id] = new Date(el.textContent + 'T00:00:00');
});

function toggleAlumnos(id) {
    const lista = document.getElementById(id);
    lista.style.display = (lista.style.display === "none" || lista.style.display === "") ? "block" : "none";
}

function cambiarSemana(curso_id, dias) {
    semanas[curso_id].setDate(semanas[curso_id].getDate() + dias);

    const yyyy = semanas[curso_id].getFullYear();
    const mm = String(semanas[curso_id].getMonth() + 1).padStart(2, '0');
    const dd = String(semanas[curso_id].getDate()).padStart(2, '0');
    const fechaStr = `${yyyy}-${mm}-${dd}`;

    // Paso 1: Actualizar el texto de la fecha
    document.getElementById(`texto_fecha_${curso_id}`).innerText = fechaStr;

    // Paso 2: Actualizar el enlace para exportar asistencia
    // Esta es la línea clave que faltaba
    const linkAsistencia = document.getElementById(`link_asistencia_${curso_id}`);
    linkAsistencia.href = `/exportar_asistencia/${curso_id}?inicio=${fechaStr}`;
}