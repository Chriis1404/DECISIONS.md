using System.Net;
using System.Net.Sockets;
using System.Text;

var host = "127.0.0.1";
var port = 5001;

using var udp = new UdpClient();
// En UDP no hay "Connect", definimos el destino
var server = new IPEndPoint(IPAddress.Parse(host), port);

Console.WriteLine($"[UDP] Listo para enviar a {host}:{port}");

foreach (var msg in new[] { "Mensaje 1 UDP", "Mensaje 2 UDP", "Mensaje 3 UDP" })
{
    var bytes = Encoding.UTF8.GetBytes(msg);
    
    Console.WriteLine($"[UDP] Enviando: {msg}");
    await udp.SendAsync(bytes, bytes.Length, server);
    
    // Esperar respuesta (Eco) con timeout manual simple
    try 
    {
        var receiveTask = udp.ReceiveAsync();
        if (await Task.WhenAny(receiveTask, Task.Delay(2000)) == receiveTask)
        {
            var result = await receiveTask;
            Console.WriteLine($"[UDP] Eco recibido: {Encoding.UTF8.GetString(result.Buffer)}");
        }
        else
        {
            Console.WriteLine("⚠️ [UDP] Tiempo de espera agotado (Paquete perdido o servidor apagado).");
        }
    }
    catch (Exception ex)
    {
        Console.WriteLine($"[UDP] Error: {ex.Message}");
    }

    await Task.Delay(1000);
}
