using System.Net;
using System.Net.Sockets;
using System.Text;

var port = 5001;
using var udp = new UdpClient(port);
Console.WriteLine($"[UDP] Servidor escuchando en 0.0.0.0:{port}");

while (true)
{
    // ReceiveAsync devuelve un objeto con el Buffer y el RemoteEndPoint
    var result = await udp.ReceiveAsync();
    var text = Encoding.UTF8.GetString(result.Buffer);
    
    Console.WriteLine($"[UDP] De {result.RemoteEndPoint} -> {text}");
    
    // Eco: devolver los mismos bytes al remitente
    await udp.SendAsync(result.Buffer, result.Buffer.Length, result.RemoteEndPoint); 
}
