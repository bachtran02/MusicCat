import typing as t
import lightbulb
import hikari
from hikari.impl import MessageActionRowBuilder

from bot.constants import COLOR_DICT
from bot.utils import player_bar

PLAYER_BUTTONS = [
    {
        'id': 'previous',
        'emoji': '⏮️',
    },
    {
        'id': 'playpause',
        'emoji': '⏯️',
    },
        {
        'id': 'stop',
        'emoji': '⏹️',
    },
    {
        'id': 'next',
        'emoji': '⏭️',
    },
]

async def generate_rows(bot: lightbulb.BotApp) -> t.Iterable[MessageActionRowBuilder]:
    """Generate 2 action rows with 4 buttons each."""

    rows: t.List[MessageActionRowBuilder] = []

    row = bot.rest.build_message_action_row()

    for i, button in enumerate(PLAYER_BUTTONS):
        if i % 4 == 0 and i != 0:
            rows.append(row)
            row = bot.rest.build_message_action_row()

        # We use an enclosing scope here so that we can easily chain
        # method calls of the action row.
        (
            row.add_interactive_button(
                hikari.ButtonStyle.SECONDARY,
                button['id'],
                emoji=button['emoji'],
            )
        )

    rows.append(row)
    return rows


async def handle_responses(
    bot: lightbulb.BotApp, author: hikari.User, message: hikari.Message,
) -> None:
    """Watches for events, and handles responding to them."""

    with bot.stream(hikari.InteractionCreateEvent, timeout=300).filter(
        lambda e: (
            isinstance(e.interaction, hikari.ComponentInteraction)  # a component interaction is a button interaction.
            and e.interaction.user == author  # Make sure the command author hit the button.
            and e.interaction.message == message  # Make sure the button was attached to our message.
        )
    ) as stream:
        async for event in stream:
            cid = event.interaction.custom_id
            player = bot.d.lavalink.player_manager.get(event.interaction.guild_id)
            
            if cid == 'playpause':
                await player.set_pause(not player.paused) 
            elif cid == 'stop':
                await player.stop()
            elif cid == 'next': 
                await player.skip()
            elif cid == 'previous':
                # play previous track
                pass

            if not player.is_playing:
                embed = hikari.Embed(
                    description='**No track to play!**',
                    color=COLOR_DICT['YELLOW'],
                )
            else:
                body = f'**Streaming:** [{player.current.title}]({player.current.uri})' + '\n'
                body += player_bar(player)
                body += f'Requested - <@!{player.current.requester}>'
                embed = hikari.Embed(
                    description=body,
                    color=COLOR_DICT['GREEN'],
                )

            # If we haven't responded to the interaction yet, we
            # need to create the initial response. Otherwise, we
            # need to edit the initial response.
            try:
                await event.interaction.create_initial_response(
                    hikari.ResponseType.MESSAGE_UPDATE,
                    embed=embed,
                )
            except hikari.NotFoundError:
                await event.interaction.edit_initial_response(
                    embed=embed,
                )

    # remove the buttons after timeout
    await message.edit(components=[])
