"""LAVALINK CONFIG"""
LAVALINK_HOST: str = 'lavalink'
LAVALINK_PORT: int = 2333
LAVALINK_PASSWORD: str = 'youshallnotpass'
LAVALINK_NODES: list = [
    {'name': 'default-node'},
    {'name': 'backup-node'},
]

"""REDIS CONFIG"""
REDIS_HOST: str = 'music_redis'
REDIS_PORT: int = 6379
