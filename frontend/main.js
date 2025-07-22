const scoreDiv = document.getElementById("score");
const resultadoDiv = document.getElementById("resultado");

// 🔁 Altere se o backend estiver em outro IP/porta
const socket = new WebSocket("ws://localhost:8765");

socket.onopen = () => {
  console.log("✅ Conectado ao servidor");
  resultadoDiv.textContent = "Aguardando dados...";
  resultadoDiv.className = "text-3xl font-bold p-4 rounded-xl bg-gray-700";
};

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);

  const score = parseFloat(data.score).toFixed(4);
  const resultado = data.resultado;

  console.log(score, resultado);

  scoreDiv.textContent = score;

  if (resultado) {
    resultadoDiv.textContent = "🚨 Queda detectada!";
    resultadoDiv.className = "text-3xl font-bold p-4 rounded-xl bg-red-600";
  } else {
    resultadoDiv.textContent = "✅ Sem queda";
    resultadoDiv.className = "text-3xl font-bold p-4 rounded-xl bg-green-600";
  }
};

socket.onclose = () => {
  console.log("❌ Conexão encerrada");
  resultadoDiv.textContent = "Conexão perdida";
  resultadoDiv.className = "text-3xl font-bold p-4 rounded-xl bg-gray-500";
};
