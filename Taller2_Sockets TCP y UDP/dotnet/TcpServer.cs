using System.Net;
using System.Net.Sockets;
using System.Text;

var host = IPAddress.Any;
var port = 5000;
var listener = new TcpListener(host, port);
listener.Start();
Console.WriteLine($"[TCP] Servidor escuchando en {host}:{port}");

while (true)
{
    var client = await listener.AcceptTcpClientAsync();
    _ = HandleClientAsync(client);
}

static async Task HandleClientAsync(TcpClient client)
{
    var remote = client.Client.RemoteEndPoint;
    Console.WriteLine($"[TCP] Conexión de {remote}");
    using (client)
    using (var stream = client.GetStream())
    {
        var buffer = new byte[1024];
        int n;
        // Leemos del stream y escribimos lo mismo de vuelta (Eco)
        while ((n = await stream.ReadAsync(buffer.AsMemory(0, buffer.Length))) > 0)
        {
            var data = buffer.AsMemory(0, n);
            Console.WriteLine($"[TCP] Recibido {n} bytes: {Encoding.UTF8.GetString(data.Span)}");
            await stream.WriteAsync(data); // Eco
        }
    }
    Console.WriteLine($"[TCP] Cliente {remote} desconectado");
}
