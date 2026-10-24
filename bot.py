
import os
import asyncio
import discord
from discord.ext import commands, tasks
from discord import app_commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class ALGBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()
        voice_reconnect.start()

bot = ALGBot(command_prefix="!", intents=intents)

voice_247 = {}
ticket_category_name = "Tickets"


@bot.event
async def on_ready():
    print(f"ALG Bot is online: {bot.user}")
    await bot.change_presence(
        activity=discord.Game(name="Alakonda Gaming | /help")
    )


@bot.tree.command(name="about", description="معلومات عن ALG Bot")
async def about(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🎮 أنا ALG Bot — Alakonda Gaming!",
        ephemeral=True
    )


@bot.tree.command(name="alakonda", description="معلومات Alakonda Gaming")
async def alakonda(interaction: discord.Interaction):
    await interaction.response.send_message(
        "🎮 **Alakonda Gaming**\n"
        "YouTube: https://www.youtube.com/@AlakondaGaming\n"
        "Kick: https://kick.com/alakondagaming1"
    )


@bot.tree.command(name="social", description="روابط التواصل")
async def social(interaction: discord.Interaction):
    await interaction.response.send_message(
        "📺 YouTube: https://www.youtube.com/@AlakondaGaming\n"
        "🟢 Kick: https://kick.com/alakondagaming1"
    )


@bot.tree.command(name="ping", description="فحص سرعة البوت")
async def ping(interaction: discord.Interaction):
    ms = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Ping: {ms} ms")


@bot.tree.command(name="server", description="معلومات السيرفر")
async def server(interaction: discord.Interaction):
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "هذا الأمر يعمل داخل السيرفر فقط.", ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"**{guild.name}**\n"
        f"الأعضاء: {guild.member_count}"
    )


@bot.tree.command(name="rules", description="عرض القوانين")
async def rules(interaction: discord.Interaction):
    await interaction.response.send_message(
        "📜 **قوانين السيرفر**\n"
        "1. الاحترام بين الجميع.\n"
        "2. ممنوع السبام.\n"
        "3. ممنوع الإزعاج.\n"
        "4. اتبع تعليمات الإدارة."
    )


@bot.tree.command(name="join", description="دخول البوت إلى قناتك الصوتية")
async def join(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("استخدم الأمر داخل السيرفر.")
        return

    if not interaction.user.voice:
        await interaction.response.send_message(
            "ادخل قناة صوتية أولًا.", ephemeral=True
        )
        return

    channel = interaction.user.voice.channel
    voice = interaction.guild.voice_client

    if voice:
        await voice.move_to(channel)
    else:
        await channel.connect(reconnect=True, self_deaf=True)

    await interaction.response.send_message(f"🔊 دخلت {channel.mention}")


@bot.tree.command(name="leave", description="إخراج البوت من القناة الصوتية")
async def leave(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("استخدم الأمر داخل السيرفر.")
        return

    voice_247.pop(interaction.guild.id, None)
    voice = interaction.guild.voice_client

    if voice:
        await voice.disconnect(force=True)
        await interaction.response.send_message("👋 خرجت من القناة الصوتية.")
    else:
        await interaction.response.send_message("أنا لست في قناة صوتية.")


@bot.tree.command(name="247", description="تفعيل أو إيقاف وضع 24/7")
@app_commands.describe(enabled="تفعيل أو إيقاف الوضع")
async def always_on(interaction: discord.Interaction, enabled: bool):
    if not interaction.guild:
        await interaction.response.send_message("استخدم الأمر داخل السيرفر.")
        return

    if not interaction.user.voice:
        await interaction.response.send_message(
            "ادخل القناة الصوتية التي تريدني أن أبقى فيها أولًا.",
            ephemeral=True
        )
        return

    guild_id = interaction.guild.id
    channel = interaction.user.voice.channel

    if enabled:
        voice_247[guild_id] = channel.id
        voice = interaction.guild.voice_client

        if voice:
            await voice.move_to(channel)
        else:
            await channel.connect(reconnect=True, self_deaf=True)

        await interaction.response.send_message(
            "🔁 تم تفعيل وضع 24/7. سأحاول إعادة الاتصال عند الانقطاع."
        )
    else:
        voice_247.pop(guild_id, None)
        await interaction.response.send_message("تم إيقاف وضع 24/7.")


@tasks.loop(seconds=30)
async def voice_reconnect():
    for guild_id, channel_id in list(voice_247.items()):
        guild = bot.get_guild(guild_id)
        if guild is None:
            continue

        channel = guild.get_channel(channel_id)
        if not isinstance(channel, discord.VoiceChannel):
            continue

        voice = guild.voice_client

        try:
            if voice is None:
                await channel.connect(reconnect=True, self_deaf=True)
            elif not voice.is_connected():
                await voice.disconnect(force=True)
                await channel.connect(reconnect=True, self_deaf=True)
        except (discord.DiscordException, asyncio.TimeoutError) as error:
            print(f"Voice reconnect error: {error}")


@voice_reconnect.before_loop
async def before_voice_reconnect():
    await bot.wait_until_ready()


def admin_only():
    return app_commands.checks.has_permissions(administrator=True)


@bot.tree.command(name="clear", description="حذف رسائل من القناة")
@admin_only()
@app_commands.describe(amount="عدد الرسائل (1 إلى 100)")
async def clear(interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100]):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 تم حذف {len(deleted)} رسالة.")


@bot.tree.command(name="kick", description="طرد عضو")
@admin_only()
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "لم يُذكر سبب"):
    if member == interaction.user or member == interaction.guild.owner:
        await interaction.response.send_message("لا يمكن طرد هذا العضو.", ephemeral=True)
        return

    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 تم طرد {member.mention}. السبب: {reason}")


@bot.tree.command(name="ban", description="حظر عضو")
@admin_only()
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "لم يُذكر سبب"):
    if member == interaction.user or member == interaction.guild.owner:
        await interaction.response.send_message("لا يمكن حظر هذا العضو.", ephemeral=True)
        return

    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 تم حظر {member.mention}. السبب: {reason}")


@bot.tree.command(name="shoutout", description="إعطاء إعلان لعضو")
async def shoutout(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(
        f"⭐ تابعوا {member.mention}!"
    )


@bot.tree.command(name="stream", description="الإعلان عن بث مباشر")
@admin_only()
async def stream(interaction: discord.Interaction, game: str, link: str):
    await interaction.response.send_message(
        f"🔴 **بدأ البث!**\nاللعبة: {game}\nالرابط: {link}",
        allowed_mentions=discord.AllowedMentions.none()
    )


@bot.tree.command(name="event", description="الإعلان عن فعالية")
@admin_only()
async def event(interaction: discord.Interaction, title: str, details: str):
    await interaction.response.send_message(
        f"🎉 **{title}**\n{details}",
        allowed_mentions=discord.AllowedMentions.none()
    )


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="فتح تذكرة",
        emoji="🎫",
        style=discord.ButtonStyle.green,
        custom_id="alg_ticket_open"
    )
    async def open_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "هذا الزر يعمل داخل السيرفر فقط.", ephemeral=True
            )
            return

        existing = discord.utils.get(
            guild.text_channels,
            name=f"ticket-{interaction.user.id}"
        )
        if existing:
            await interaction.response.send_message(
                f"لديك تذكرة مفتوحة: {existing.mention}",
                ephemeral=True
            )
            return

        category = discord.utils.get(
            guild.categories, name=ticket_category_name
        )
        if category is None:
            category = await guild.create_category(ticket_category_name)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.id}",
            category=category,
            overwrites=overwrites
        )

        await channel.send(
            f"{interaction.user.mention} أهلًا بك! اشرح مشكلتك هنا.",
            view=CloseTicketView()
        )
        await interaction.response.send_message(
            f"✅ تم إنشاء تذكرتك: {channel.mention}",
            ephemeral=True
        )


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="إغلاق التذكرة",
        emoji="🔒",
        style=discord.ButtonStyle.red,
        custom_id="alg_ticket_close"
    )
    async def close_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "لا يمكن إغلاق هذه القناة.", ephemeral=True
            )
            return

        if not channel.name.startswith("ticket-"):
            await interaction.response.send_message(
                "هذا ليس روم تذكرة.", ephemeral=True
            )
            return

        if not interaction.user.guild_permissions.manage_channels:
            owner_id = channel.name.removeprefix("ticket-")
            if not owner_id.isdigit() or interaction.user.id != int(owner_id):
                await interaction.response.send_message(
                    "فقط صاحب التذكرة أو الإدارة يمكنه إغلاقها.",
                    ephemeral=True
                )
                return

        await interaction.response.send_message(
            "🔒 سيتم إغلاق التذكرة بعد 3 ثوانٍ."
        )
        await asyncio.sleep(3)
        await channel.delete(reason="Ticket closed")


@bot.tree.command(name="setup_ticket", description="إنشاء لوحة التذاكر")
@admin_only()
async def setup_ticket(interaction: discord.Interaction):
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    await interaction.response.send_message(
        "🎫 **الدعم الفني**\nاضغط على الزر لفتح تذكرة.",
        view=TicketView()
    )


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    if isinstance(error, app_commands.MissingPermissions):
        message = "❌ هذا الأمر خاص بالإدارة."
    else:
        print(f"Command error: {error}")
        message = "حدث خطأ أثناء تنفيذ الأمر."

    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


if not TOKEN:
    raise RuntimeError(
        "لم يتم العثور على DISCORD_TOKEN. أضفه في إعدادات الاستضافة."
    )

bot.run(TOKEN)
