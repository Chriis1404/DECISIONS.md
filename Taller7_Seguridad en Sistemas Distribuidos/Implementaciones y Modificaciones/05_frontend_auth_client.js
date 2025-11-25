// Variable para almacenar el token en memoria/localStorage
let JWT_TOKEN = localStorage.getItem("ecomarket_token");

// Función que actualiza la interfaz (Botones Login/Logout)
function updateUI() {
    // ... lógica para mostrar/ocultar botones ...
}

// Función wrapper para hacer peticiones autenticadas (Inyecta el Header)
async function authFetch(url, options = {}) {
    if (!JWT_TOKEN) {
        showToast("🔒 Inicia sesión para realizar esta acción", "warning");
        throw new Error("No token");
    }
    options.headers = options.headers || {};
    options.headers["Authorization"] = "Bearer " + JWT_TOKEN; // <--- Header Clave
    return fetch(url, options);
}

// Función de Login Manual
async function loginPrompt() {
    // ... prompt de usuario y contraseña ...
    const res = await fetch("/login", { ... });
    if(res.ok) {
        const data = await res.json();
        JWT_TOKEN = data.access_token;
        localStorage.setItem("ecomarket_token", JWT_TOKEN); // Guardado persistente
        updateUI();
    }
}
