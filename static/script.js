function copiar(id) {
    const elem = document.getElementById(id);
    navigator.clipboard.writeText(elem.value).then(() => {
        alert('¡Copiado!');
    }).catch(() => {
        // Fallback
        elem.select();
        document.execCommand('copy');
        alert('¡Copiado!');
    });
}

function compartir(texto) {
    if (navigator.share) {
        navigator.share({ text: texto }).catch(console.error);
    } else {
        alert('Comparte manualmente: ' + texto);
    }
}

// Detectar hora local y highlight
document.addEventListener('DOMContentLoaded', () => {
    const hora = new Date().getHours();
    let activeId;
    if (hora < 12) activeId = 'saludo-dias';
    else if (hora < 18) activeId = 'saludo-tardes';
    else activeId = 'saludo-noches';
    document.getElementById(activeId).classList.add('highlight');
});

// Refrescar
document.getElementById('refrescar').addEventListener('click', () => location.reload());