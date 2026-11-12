// Frontend de la Tienda Online.
// Se comunica con la API de FastAPI exclusivamente mediante peticiones HTTP (fetch).

// ---------------------------------------------------------------------------
// Dirección de la API: se puede cambiar desde la cabecera de la página.
// Para usar la API de otro equipo: http://<IP_DEL_SERVIDOR>:8000
// ---------------------------------------------------------------------------
const URL_POR_DEFECTO = "http://localhost:8000";
let BASE_URL = leerUrlGuardada() || URL_POR_DEFECTO;

function leerUrlGuardada() {
  try { return localStorage.getItem("tienda_api_url"); } catch { return null; }
}
function guardarUrl(url) {
  try { localStorage.setItem("tienda_api_url", url); } catch { /* sin almacenamiento */ }
}

// ---------------------------------------------------------------------------
// PETICIONES A LA API
// Todas las llamadas pasan por pedir(), que envía la petición, comprueba el
// código de estado HTTP y devuelve el JSON (o lanza un error con el "detail").
// ---------------------------------------------------------------------------
async function pedir(metodo, ruta, cuerpo) {
  const opciones = { method: metodo, headers: {} };
  if (cuerpo !== undefined) {
    opciones.headers["Content-Type"] = "application/json";
    opciones.body = JSON.stringify(cuerpo);
  }

  let respuesta;
  try {
    respuesta = await fetch(BASE_URL + ruta, opciones);
  } catch {
    throw new Error(`No se pudo conectar con la API en ${BASE_URL}`);
  }

  // 204 No Content (p. ej. DELETE) no trae cuerpo
  const datos = respuesta.status === 204 ? null : await respuesta.json().catch(() => null);

  if (!respuesta.ok) {
    throw new Error(`Error ${respuesta.status}: ${describirDetalle(datos)}`);
  }
  return datos;
}

// FastAPI devuelve {"detail": "texto"} en errores propios y
// {"detail": [{loc, msg}, ...]} cuando falla la validación de Pydantic (422).
function describirDetalle(datos) {
  if (!datos || datos.detail === undefined) return "respuesta inesperada del servidor";
  if (typeof datos.detail === "string") return datos.detail;
  return datos.detail.map((e) => `${e.loc.slice(1).join(".") || "datos"}: ${e.msg}`).join("; ");
}

// Un método por endpoint de la API
const api = {
  listarProductos:  ()       => pedir("GET",    "/productos"),                 // GET    /productos
  crearProducto:    (datos)  => pedir("POST",   "/productos", datos),          // POST   /productos
  eliminarProducto: (id)     => pedir("DELETE", `/productos/${id}`),           // DELETE /productos/{producto_id}
  listarUsuarios:   ()       => pedir("GET",    "/usuarios"),                  // GET    /usuarios
  crearUsuario:     (datos)  => pedir("POST",   "/usuarios", datos),           // POST   /usuarios
  crearPedido:      (datos)  => pedir("POST",   "/pedidos", datos),            // POST   /pedidos
  pedidosDeCliente: (id)     => pedir("GET",    `/usuarios/${id}/pedidos`),    // GET    /usuarios/{cliente_id}/pedidos
};

// ---------------------------------------------------------------------------
// Estado y utilidades de interfaz
// ---------------------------------------------------------------------------
let productos = [];
let usuarios = [];

const $ = (sel) => document.querySelector(sel);
const idCorto = (id) => `<span title="${id}">${String(id).slice(0, 8)}</span>`;
const euros = (n) => n.toLocaleString("es-ES", { style: "currency", currency: "EUR" });

function escapar(texto) {
  const div = document.createElement("div");
  div.textContent = String(texto ?? "");
  return div.innerHTML;
}

let temporizadorAviso;
function avisar(mensaje, tipo = "exito") {
  const aviso = $("#aviso");
  aviso.textContent = mensaje;
  aviso.className = `aviso ${tipo}`;
  aviso.hidden = false;
  clearTimeout(temporizadorAviso);
  temporizadorAviso = setTimeout(() => (aviso.hidden = true), 5000);
}

// Ejecuta una acción y muestra el error si la API lo devuelve
async function conAviso(accion, mensajeExito) {
  try {
    const resultado = await accion();
    if (mensajeExito) avisar(mensajeExito);
    return resultado;
  } catch (e) {
    avisar(e.message, "error");
    return undefined;
  }
}

// ---------------------------------------------------------------------------
// Productos
// ---------------------------------------------------------------------------
async function cargarProductos() {
  const datos = await conAviso(api.listarProductos);
  if (!datos) return;
  productos = datos;
  pintarProductos();
  actualizarSelectoresProducto();
}

function pintarProductos() {
  const tbody = $("#tabla-productos");
  if (productos.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="vacio">No hay productos todavía</td></tr>`;
    return;
  }
  tbody.innerHTML = productos.map((p) => {
    let detalles = "";
    if (p.tipo === "electronico") detalles = `Garantía: ${p.meses_garantia} meses`;
    if (p.tipo === "ropa") detalles = `Talla ${escapar(p.talla)} · ${escapar(p.color)}`;
    return `<tr>
      <td>${idCorto(p.id)}</td>
      <td><span class="etiqueta">${p.tipo}</span></td>
      <td>${escapar(p.nombre)}</td>
      <td class="num">${euros(p.precio)}</td>
      <td class="num">${p.stock}</td>
      <td>${detalles}</td>
      <td><button class="peligro" data-eliminar="${p.id}">Eliminar</button></td>
    </tr>`;
  }).join("");
}

function mostrarCamposSegunTipo() {
  const tipo = $("#producto-tipo").value;
  document.querySelectorAll(".solo-electronico").forEach((el) => (el.hidden = tipo !== "electronico"));
  document.querySelectorAll(".solo-ropa").forEach((el) => (el.hidden = tipo !== "ropa"));
}

async function enviarProducto(evento) {
  evento.preventDefault();
  const f = new FormData(evento.target);
  const tipo = f.get("tipo");

  // Solo se envían los atributos que corresponden al tipo de producto
  const datos = {
    tipo,
    nombre: f.get("nombre"),
    precio: Number(f.get("precio")),
    stock: Number(f.get("stock")),
  };
  if (tipo === "electronico") datos.meses_garantia = Number(f.get("meses_garantia"));
  if (tipo === "ropa") {
    datos.talla = f.get("talla");
    datos.color = f.get("color");
  }

  const creado = await conAviso(() => api.crearProducto(datos));
  if (creado) {
    avisar(`Producto "${creado.nombre}" creado`);
    evento.target.reset();
    mostrarCamposSegunTipo();
    cargarProductos();
  }
}

async function eliminarProducto(id) {
  const producto = productos.find((p) => p.id === id);
  if (!confirm(`¿Eliminar "${producto?.nombre ?? id}"?`)) return;
  try {
    await api.eliminarProducto(id);
    avisar(`Producto eliminado`);
    cargarProductos();
  } catch (e) {
    avisar(e.message, "error");
  }
}

// ---------------------------------------------------------------------------
// Usuarios
// ---------------------------------------------------------------------------
async function cargarUsuarios() {
  const datos = await conAviso(api.listarUsuarios);
  if (!datos) return;
  usuarios = datos;
  pintarUsuarios();
  actualizarSelectoresCliente();
}

function pintarUsuarios() {
  const tbody = $("#tabla-usuarios");
  if (usuarios.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="vacio">No hay usuarios todavía</td></tr>`;
    return;
  }
  tbody.innerHTML = usuarios.map((u) => `<tr>
      <td>${idCorto(u.id)}</td>
      <td>${escapar(u.nombre)}</td>
      <td>${escapar(u.email)}</td>
      <td><span class="etiqueta">${u.es_admin ? "Administrador" : "Cliente"}</span></td>
    </tr>`).join("");
}

async function enviarUsuario(evento) {
  evento.preventDefault();
  const f = new FormData(evento.target);
  const datos = {
    tipo: f.get("tipo"),
    nombre: f.get("nombre"),
    email: f.get("email"),
    direccion_postal: f.get("direccion_postal") || null,
  };
  const creado = await conAviso(() => api.crearUsuario(datos));
  if (creado) {
    avisar(`Usuario "${creado.nombre}" creado`);
    evento.target.reset();
    cargarUsuarios();
  }
}

// ---------------------------------------------------------------------------
// Pedidos
// ---------------------------------------------------------------------------
function opcionesClientes() {
  const clientes = usuarios.filter((u) => !u.es_admin);
  if (clientes.length === 0) return `<option value="">— No hay clientes —</option>`;
  return clientes.map((u) => `<option value="${u.id}">${escapar(u.nombre)} (${escapar(u.email)})</option>`).join("");
}

function opcionesProductos() {
  if (productos.length === 0) return `<option value="">— No hay productos —</option>`;
  return productos
    .map((p) => `<option value="${p.id}">${escapar(p.nombre)} (${euros(p.precio)}, stock ${p.stock})</option>`)
    .join("");
}

function actualizarSelectoresCliente() {
  for (const id of ["#pedido-cliente", "#consulta-cliente"]) {
    const select = $(id);
    const anterior = select.value;
    select.innerHTML = opcionesClientes();
    if ([...select.options].some((o) => o.value === anterior)) select.value = anterior;
  }
}

function actualizarSelectoresProducto() {
  document.querySelectorAll(".linea-producto").forEach((select) => {
    const anterior = select.value;
    select.innerHTML = opcionesProductos();
    if ([...select.options].some((o) => o.value === anterior)) select.value = anterior;
  });
}

function anadirLinea() {
  const linea = $("#plantilla-linea").content.firstElementChild.cloneNode(true);
  linea.querySelector(".linea-producto").innerHTML = opcionesProductos();
  linea.querySelector(".quitar").addEventListener("click", () => {
    if (document.querySelectorAll(".linea").length > 1) linea.remove();
  });
  $("#lineas-pedido").appendChild(linea);
}

async function enviarPedido(evento) {
  evento.preventDefault();
  const items = [...document.querySelectorAll(".linea")].map((linea) => ({
    producto_id: linea.querySelector(".linea-producto").value,
    cantidad: Number(linea.querySelector(".linea-cantidad").value),
  }));
  const datos = { cliente_id: $("#pedido-cliente").value, items };

  const pedido = await conAviso(() => api.crearPedido(datos));
  if (pedido) {
    avisar(`Pedido creado. Total: ${euros(pedido.total)}`);
    $("#lineas-pedido").innerHTML = "";
    anadirLinea();
    cargarProductos(); // el stock ha cambiado
    $("#consulta-cliente").value = pedido.cliente_id;
    consultarPedidos();
  }
}

async function consultarPedidos(evento) {
  evento?.preventDefault();
  const clienteId = $("#consulta-cliente").value;
  if (!clienteId) return;
  const pedidos = await conAviso(() => api.pedidosDeCliente(clienteId));
  if (!pedidos) return;

  const contenedor = $("#lista-pedidos");
  if (pedidos.length === 0) {
    contenedor.innerHTML = `<p class="vacio">Este cliente no tiene pedidos</p>`;
    return;
  }
  contenedor.innerHTML = pedidos.map((p) => `
    <div class="pedido">
      <div class="pedido-cabecera">
        <span>Pedido ${idCorto(p.id)} <span class="pedido-fecha">${new Date(p.fecha).toLocaleString("es-ES")}</span></span>
        <span>${euros(p.total)}</span>
      </div>
      <table>
        <thead><tr><th>Producto</th><th>Precio</th><th>Cant.</th><th>Subtotal</th></tr></thead>
        <tbody>
          ${p.items.map((i) => `<tr>
            <td>${escapar(i.nombre)}</td>
            <td class="num">${euros(i.precio_unitario)}</td>
            <td class="num">${i.cantidad}</td>
            <td class="num">${euros(i.subtotal)}</td>
          </tr>`).join("")}
        </tbody>
      </table>
    </div>`).join("");
}

// ---------------------------------------------------------------------------
// Conexión, pestañas e inicio
// ---------------------------------------------------------------------------
async function conectar() {
  const estado = $("#estado-api");
  estado.textContent = "Conectando…";
  estado.className = "estado";
  try {
    await pedir("GET", "/");
    estado.textContent = "Conectado";
    estado.classList.add("ok");
  } catch {
    estado.textContent = "Sin conexión";
    estado.classList.add("ko");
  }
  await Promise.all([cargarProductos(), cargarUsuarios()]);
}

function cambiarPestana(nombre) {
  document.querySelectorAll(".pestanas button").forEach((b) => b.classList.toggle("activa", b.dataset.tab === nombre));
  document.querySelectorAll(".tab").forEach((t) => (t.hidden = t.id !== `tab-${nombre}`));
  if (nombre === "productos") cargarProductos();
  if (nombre === "usuarios") cargarUsuarios();
  if (nombre === "pedidos") { cargarProductos(); cargarUsuarios(); }
}

document.addEventListener("DOMContentLoaded", () => {
  $("#api-url").value = BASE_URL;
  $("#form-api").addEventListener("submit", (e) => {
    e.preventDefault();
    BASE_URL = $("#api-url").value.trim().replace(/\/+$/, "");
    guardarUrl(BASE_URL);
    conectar();
  });

  document.querySelectorAll(".pestanas button").forEach((b) =>
    b.addEventListener("click", () => cambiarPestana(b.dataset.tab)));
  document.querySelectorAll("[data-recargar]").forEach((b) =>
    b.addEventListener("click", () => (b.dataset.recargar === "productos" ? cargarProductos() : cargarUsuarios())));

  $("#producto-tipo").addEventListener("change", mostrarCamposSegunTipo);
  $("#form-producto").addEventListener("submit", enviarProducto);
  $("#tabla-productos").addEventListener("click", (e) => {
    const id = e.target.dataset.eliminar;
    if (id) eliminarProducto(id);
  });

  $("#form-usuario").addEventListener("submit", enviarUsuario);
  $("#form-pedido").addEventListener("submit", enviarPedido);
  $("#anadir-linea").addEventListener("click", anadirLinea);
  $("#form-consulta").addEventListener("submit", consultarPedidos);

  anadirLinea();
  conectar();
});
