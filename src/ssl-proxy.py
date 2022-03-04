import asyncio
import ssl

ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(certfile="/run/secrets/nginx/nginx_be.pem", keyfile="/run/secrets/nginx/nginx_be.key")


async def read_client_data(client_reader, nginx_writer):
    while True:
        client_data = await asyncio.wait_for(client_reader.read(100), timeout=5)
        nginx_writer.write(client_data)
        if client_data:
            print('client_data - ', client_reader._transport.get_extra_info("peername"), ':', len(client_data), client_data)
            await nginx_writer.drain()


async def read_nginx_reasponse(nginx_reader, client_writer, client_reader):
    while True:
        nginx_data = await asyncio.wait_for(nginx_reader.read(100), timeout=5)
        client_writer.write(nginx_data)
        if nginx_data:
            print('nginx_data - ', client_reader._transport.get_extra_info("peername"), ': ', len(nginx_data), nginx_data)
            await client_writer.drain()


loop = asyncio.get_event_loop()


async def client_connected_cb(client_reader, client_writer):
    print('====CLIENT IP/PORT====', client_reader._transport.get_extra_info('peername'))
    # if client_reader._transport.get_extra_info('peername') != '192.168.128.91':
    #     client_reader._transport.close()
    nginx_reader, nginx_writer = await asyncio.open_connection(host='devsync.myonlinedata.net', port=80, ssl=None)
    t1 = loop.create_task(read_client_data(client_reader, nginx_writer))
    t2 = loop.create_task(read_nginx_reasponse(nginx_reader, client_writer, client_reader))
    await t1
    await t2


def main():
    # loop = asyncio.get_running_loop()
    server = asyncio.start_server(
        client_connected_cb, host='0.0.0.0', port=443, ssl=ssl_context)
    server = loop.run_until_complete(server)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    # async with server:
    #     await server.serve_forever()


# asyncio.run(main())
main()
