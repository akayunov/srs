import asyncio
import pdb
import ssl

ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain(certfile="/run/secrets/nginx/nginx_be.pem", keyfile="/run/secrets/nginx/nginx_be.key")

# HOSTNAME = 'devsync.myonlinedata.net'
HOSTNAME = 'nginx'


async def read_client_data(client_reader, nginx_writer, client_info):
    while True:
        try:
            # client_data = await asyncio.wait_for(client_reader.read(100), timeout=5)
            # import pdb;pdb.set_trace()
            client_data = await client_reader.read(100)
            if client_data:
                nginx_writer.write(client_data)
                print('client_data - ', client_info, ':', len(client_data), client_data)
                await nginx_writer.drain()
            else:
                # print('client_data - sleep', client_info,)
                await asyncio.sleep(1)
        except BaseException as e:
            print('client_data:', client_info, e)
            break


async def read_nginx_reasponse(nginx_reader, client_writer, client_info):
    while True:
        try:
            # nginx_data = await asyncio.wait_for(nginx_reader.read(100), timeout=5)
            # import pdb;pdb.set_trace()
            nginx_data = await nginx_reader.read(100)
            if nginx_data:
                client_writer.write(nginx_data)
                print('nginx_data - ', client_info, ': ', len(nginx_data), nginx_data)
                await client_writer.drain()
            else:
                # print('nginx_data - sleep', client_info, )
                await asyncio.sleep(1)
        except BaseException as e:
            print('nginx_data:', client_info, e)
            break


loop = asyncio.get_event_loop()


async def client_connected_cb(client_reader, client_writer):
    client_info = client_writer.get_extra_info('peername')
    print('====CLIENT IP/PORT====', client_info)
    # if client_reader._transport.get_extra_info('peername') != '192.168.128.91':
    #     client_reader._transport.close()
    nginx_reader, nginx_writer = await asyncio.open_connection(host=HOSTNAME, port=80, ssl=None)
    t1 = loop.create_task(read_client_data(client_reader, nginx_writer, client_info))
    t2 = loop.create_task(read_nginx_reasponse(nginx_reader, client_writer, client_info))
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
