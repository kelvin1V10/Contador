import React, { useEffect, useRef, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default function App() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [peopleCount, setPeopleCount] = useState(0);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    // Pega a webcam
    navigator.mediaDevices
      .getUserMedia({ video: true })
      .then((stream) => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      })
      .catch((err) => alert("Erro ao acessar webcam: " + err.message));
  }, []);

  useEffect(() => {
    if (!videoRef.current) return;

    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onopen = () => console.log("WebSocket conectado");

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setPeopleCount(data.count);
      setHistory((prev) => [
        ...prev.slice(-49),
        { time: new Date().toLocaleTimeString(), count: data.count },
      ]);

      if (!canvasRef.current || !videoRef.current) return;
      const ctx = canvasRef.current.getContext("2d");
      ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);

      data.boxes.forEach((box, i) => {
        ctx.strokeStyle = "lime";
        ctx.lineWidth = 3;
        ctx.strokeRect(box.x1, box.y1, box.x2 - box.x1, box.y2 - box.y1);
        ctx.font = "18px Arial";
        ctx.fillStyle = "lime";
        ctx.fillText(`Pessoa ${i + 1}`, box.x1, box.y1 - 10);
      });
    };

    ws.onclose = () => console.log("WebSocket desconectado");

    const sendFrame = () => {
      if (!videoRef.current) return;
      const width = videoRef.current.videoWidth;
      const height = videoRef.current.videoHeight;

      if (width === 0 || height === 0) {
        return; // vídeo não carregou ainda
      }

      const canvas = document.createElement("canvas");
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(videoRef.current, 0, 0, width, height);
      canvas.toBlob(
        (blob) => {
          if (!blob) return;
          const reader = new FileReader();
          reader.onloadend = () => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(reader.result);
            }
          };
          reader.readAsDataURL(blob);
        },
        "image/jpeg",
        0.7
      );
    };

    const interval = setInterval(sendFrame, 200);

    return () => {
      clearInterval(interval);
      ws.close();
    };
  }, []);

  const data = {
    labels: history.map((h) => h.time),
    datasets: [
      {
        label: "Contagem de Pessoas",
        data: history.map((h) => h.count),
        fill: false,
        backgroundColor: "red",
        borderColor: "red",
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: { position: "top" },
      title: { display: true, text: "Histórico de Pessoas Detectadas" },
    },
    scales: {
      y: {
        beginAtZero: true,
        precision: 0,
      },
    },
  };

  return (
    <div style={{ position: "relative", width: 640, margin: "auto" }}>
      <h1>Contador de Pessoas - React Frontend</h1>
      <div style={{ position: "relative" }}>
        <video
          ref={videoRef}
          width={640}
          height={480}
          autoPlay
          muted
          style={{ borderRadius: 8 }}
        />
        <canvas
          ref={canvasRef}
          width={640}
          height={480}
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            pointerEvents: "none",
            borderRadius: 8,
          }}
        />
      </div>
      <p>Pessoas detectadas agora: {peopleCount}</p>
      <Line options={options} data={data} />
    </div>
  );
}