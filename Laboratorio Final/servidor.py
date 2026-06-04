
from flask import Flask, request, render_template_string, jsonify

# ---------------- CREAR APP ----------------

app = Flask(__name__)

# ---------------- API KEY ----------------

API_KEY = "nevera123"

# ---------------- DATOS ----------------

datos = {
    "alerta": "NINGUNA",
    "temperatura": 0,
    "humedad": 0,
    "movimiento": 0,
    "estado_puerta": "CERRADA",
    "estado_bloqueo": "DESBLOQUEADA",
    "setpoint": 18.0
}

# ---------------- RECIBIR DATOS DEL ESP32 ----------------

@app.route('/datos', methods=['POST'])
def recibir():

    global datos

    if request.headers.get("X-API-Key") != API_KEY:
        return "No autorizado", 401

    nuevos_datos = request.json

    datos["alerta"] = nuevos_datos.get("alerta", datos["alerta"])
    datos["temperatura"] = nuevos_datos.get("temperatura", datos["temperatura"])
    datos["humedad"] = nuevos_datos.get("humedad", datos["humedad"])
    datos["movimiento"] = nuevos_datos.get("movimiento", datos["movimiento"])
    datos["estado_puerta"] = nuevos_datos.get("estado_puerta", datos["estado_puerta"])
    datos["estado_bloqueo"] = nuevos_datos.get("estado_bloqueo", datos["estado_bloqueo"])

    print(datos)

    return "OK"

# ---------------- GUARDAR SETPOINT ----------------

@app.route('/setpoint', methods=['POST'])
def guardar_setpoint():

    try:
        datos["setpoint"] = float(request.form["setpoint"])
    except:
        pass

    return "", 204

# ---------------- CONFIGURACIÓN PARA ESP32 ----------------

@app.route('/config')
def config():

    return jsonify({
        "setpoint": datos["setpoint"]
    })

#-------

@app.route('/estado')
def estado():

    return jsonify({
        "alerta": datos["alerta"],
        "temperatura": datos["temperatura"],
        "humedad": datos["humedad"],
        "movimiento": datos["movimiento"],
        "estado_puerta": datos["estado_puerta"],
        "estado_bloqueo": datos["estado_bloqueo"],
        "setpoint": datos["setpoint"]
    })
# ---------------- PÁGINA PRINCIPAL ----------------

@app.route('/')
def inicio():

    alerta = datos.get("alerta", "Sin datos")

    if alerta.upper() == "NORMAL":
        color_fondo = "#d4edda"
        color_borde = "#28a745"
    else:
        color_fondo = "#f8d7da"
        color_borde = "#dc3545"

    html = f"""

<!DOCTYPE html>

<html lang="es">

<head>

<meta charset="UTF-8">

<title>Nevera Médica</title>

<style>

body{{
    margin:0;
    font-family:Arial;
    background:#dfe5eb;
    text-align:center;
}}

header{{
    background:navy;
    color:white;
    padding:35px;
}}

header h1{{
    margin:0;
    font-size:38px;
}}

header p{{
    margin-top:10px;
    font-size:18px;
}}
.header-contenido{{

    max-width:1400px;
    margin:auto;

    display:flex;
    justify-content:space-between;
    align-items:center;
}}

.header-texto{{

    flex:1;
    text-align:center;
    margin-left:240px;
}}

#panel-alertas{{

    width:300px;
    min-height:120px;

    background:white;
    color:#333;

    border-radius:15px;

    padding:15px;

    font-size:16px;
    font-weight:bold;

    display:flex;
    align-items:center;
    justify-content:center;
    text-align:center;

    box-shadow:0px 4px 10px rgba(0,0,0,0.2);

    transition:0.3s;
}}

.contenido{{
    margin-top:40px;
}}

.container{{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(250px,1fr));
    gap:20px;
    padding:30px;
    max-width:1000px;
    margin:auto;
}}

.container2{{
    display:grid;
    grid-template-columns:repeat(2,1fr);
    gap:20px;
    padding:0px 30px 30px 30px;
    max-width:700px;
    margin:auto;
}}

.card{{
    background:white;
    border-radius:18px;
    padding:25px;
    box-shadow:0px 4px 10px rgba(0,0,0,0.1);
}}

.texto{{
    margin-top:10px;
    color:#555;
    font-size:12px;
}}

.setpoint input{{
    width:150px;
    padding:10px;
    text-align:center;
    font-size:18px;
    border-radius:10px;
    border:1px solid #ccc;
}}

.boton{{
    margin-top:10px;
    padding:8px 20px;
    background:navy;
    color:white;
    border:none;
    border-radius:8px;
    cursor:pointer;
}}

.boton:hover{{
    opacity:0.9;
}}
.panel-principal{{

    display:grid;
    grid-template-columns: 1fr 1fr;

    gap:20px;

    max-width:1200px;
    margin:auto;
    padding:30px;

    align-items:start;
}}

.card-izquierda{{

    background:white;
    border-radius:18px;
    padding:30px;

    box-shadow:0px 4px 10px rgba(0,0,0,0.1);

    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;

    min-height:320px;
}}

.panel-derecha{{

    display:grid;

    grid-template-columns:1fr 1fr;

    gap:15px;

    align-self:start;
}}

.card-derecha{{

    background:white;

    border-radius:18px;

    padding:15px;

    min-height:150px;

    box-shadow:0px 4px 10px rgba(0,0,0,0.1);

    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
}}

.titulo{{

    color:#1976d2;
    font-size:20px;
    font-weight:bold;
    margin-bottom:10px;
}}

.valor{{

    font-size:32px;
    font-weight:bold;
}}

.estado{{

    font-size:22px;
    font-weight:bold;
}}


</style>

</head>

<body>

<header>

    <div class="header-contenido">

        <div class="header-texto">

            <h1>Nevera Médica</h1>

            <p>Monitoreo y control de medicamentos</p>

        </div>

        <div id="panel-alertas">

            Alertas:<br>Ninguna

        </div>

    </div>

</header>

<div class="contenido">


    <div class="panel-principal">

    <div class="card-izquierda">

        <div class="titulo">
            Temperatura
        </div>

        <div class="valor" id="temperatura">
            {datos.get("temperatura")} °C
        </div>
        <div class="texto" id="setpoint">
            Setpoint: {datos.get("setpoint")} °C
        </div>

        <br><br><br>

        <div class="titulo">
            Control PID
        </div>

        <form action="/setpoint" method="POST">

            <input
                type="number"
                name="setpoint"
                step="0.1"
                value="{datos.get('setpoint')}">

            <br><br>

            <button class="boton" type="submit">
                Guardar
            </button>

        </form>

        <div class="texto">
            Temperatura deseada para la nevera
        </div>

    </div>

    <div class="panel-derecha">

        <div class="card-derecha">

            <div class="titulo">
                Humedad
            </div>

            <div class="valor" id="humedad">
                {datos.get("humedad")} %
            </div>

        </div>

        <div class="card-derecha">

            <div class="titulo">
                Estado Transporte
            </div>

            <div class="estado" id="movimiento">
                {datos.get("movimiento")}
            </div>

        </div>

        <div class="card-derecha">

            <div class="titulo">
                Estado de Bloqueo
            </div>

            <div class="estado" id="estado_bloqueo">
                {datos.get("estado_bloqueo")}
            </div>

        </div>

        <div class="card-derecha">

            <div class="titulo">
                Estado de Puerta
            </div>

            <div class="estado" id="estado_puerta">
                {datos.get("estado_puerta")}
            </div>

        </div>

    </div>

</div>

</div>
<script>

async function actualizar() {{

    let respuesta = await fetch('/estado');

    let datos = await respuesta.json();

    document.getElementById("temperatura").innerHTML =
        datos.temperatura + " °C";

    document.getElementById("setpoint").innerHTML =
        "Setpoint: " +
        datos.setpoint +
        " °C";

    document.getElementById("humedad").innerHTML =
        datos.humedad + " %";

    document.getElementById("movimiento").innerHTML =
        datos.movimiento;

    document.getElementById("estado_bloqueo").innerHTML =
        datos.estado_bloqueo;

    document.getElementById("estado_puerta").innerHTML =
        datos.estado_puerta;

    let panel = document.getElementById("panel-alertas");

    if(datos.alerta == "NINGUNA"){{

        panel.innerHTML = "Alertas:<br>Ninguna";

        panel.style.background = "white";

        panel.style.color = "#333";

    }}
    else{{

        panel.innerHTML = "Alertas:<br>" + datos.alerta;

        panel.style.background = "#dc3545";

        panel.style.color = "white";

    }}
    }}

setInterval(actualizar, 1000);

</script>

</script>
</body>

</html>

"""

    return render_template_string(html)

# ---------------- INICIAR SERVIDOR ----------------

app.run(host="0.0.0.0", port=5000)