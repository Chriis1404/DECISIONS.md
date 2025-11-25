using System.Net.Sockets;
using System.Text;

var host = "127.0.0.1";
var port = 5000;

using var client = new TcpClient();
Console.WriteLine($"[TCP] Intentando conectar a {host}:{port}...");

try 
{
    await client.ConnectAsync(host, port);
    Console.WriteLine($"[TCP] Conectado a {host}:{port}");

    using var stream = client.GetStream();
    foreach (var msg in new[] { "Hola Mundo C#", "Probando TCP", "Adiós" })
    {
        var bytes = Encoding.UTF8.GetBytes(msg);
        await stream.WriteAsync(bytes);
        Console.WriteLine($"[TCP] Enviado: {msg}");

        var buffer = new byte[1024];
        var n = await stream.ReadAsync(buffer);
        Console.WriteLine($"[TCP] Eco recibido: {Encoding.UTF8.GetString(buffer, 0, n)}");
        
        await Task.Delay(1000); // Esperar un poco entre mensajes
    }
}
catch (Exception ex)
{
    Console.WriteLine($"[TCP] Error: {ex.Message}");
}
