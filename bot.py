# Python 3.14 | discord.py 2.3+ | file: dc.py
# pip install discord.py aiohttp

import discord
import asyncio
import aiohttp
from discord import app_commands
from discord.ext import commands

TOKEN  = "YOUR_BOT_TOKEN"  # FILL
PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True

bot  = commands.Bot(command_prefix=PREFIX, intents=intents)
tree = bot.tree

EMOJI_PAYLOAD = (
    "😈👿💀☠️😡🤬😤🔥💢😒😑👹👺🤡💩🤮"
    "🦊🐺🐗🦝🐍🦎🦖🦕🐉🔱⚡🌪️💥🌊🌑" * 6
)[:2000]

SPAM_DA_TEXT = (
    "สวัสดีชาวโลกพี่มาแล้วยิงยับ💀ๆ\n"
    "ตายชะตายชะตายชะ😡"
)

active_loops: dict[int, bool] = {}

# ── REST sender โดยตรง ไม่ผ่าน interaction ──
async def rest_send(session: aiohttp.ClientSession, channel_id: int, text: str) -> bool:
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type":  "application/json",
    }
    async with session.post(url, json={"content": text}, headers=headers) as r:
        if r.status == 200:
            return True
        elif r.status == 429:
            data  = await r.json()
            retry = float(data.get("retry_after", 1.0))
            await asyncio.sleep(retry)
            return False
        else:
            return False

# ── loop flood ใช้ REST ──────────────────
async def loop_flood(channel_id: int, text: str):
    active_loops[channel_id] = True
    total = 0
    async with aiohttp.ClientSession() as session:
        while active_loops.get(channel_id, False):
            ok = await rest_send(session, channel_id, text)
            if ok:
                total += 1
                print(f"\r[loop] sent {total}", end="", flush=True)
            await asyncio.sleep(0.4)
    print(f"\n[loop] stopped — total {total}")
    active_loops.pop(channel_id, None)

# ── single flood ─────────────────────────
async def single_flood(interaction: discord.Interaction, text: str, count: int):
    count = max(1, min(count, 30))
    sent  = 0
    async with aiohttp.ClientSession() as session:
        for _ in range(count):
            ok = await rest_send(session, interaction.channel_id, text)
            if ok:
                sent += 1
            await asyncio.sleep(0.4)
    await interaction.followup.send(f"✅ ส่งแล้ว {sent}/{count}", ephemeral=True)

# ── ready ─────────────────────────────────
@bot.event
async def on_ready():
    print(f"[+] online  : {bot.user}")
    print(f"[+] servers : {len(bot.guilds)}")
    try:
        synced = await tree.sync()
        print(f"[+] synced  : {len(synced)} slash commands")
    except Exception as e:
        print(f"[!] sync failed: {e}")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="STAR SHOP 🔥"
        )
    )

# ══════════════════════════════════════════
#  slash commands
# ══════════════════════════════════════════
@tree.command(name="spam", description="ส่ง emoji payload")
@app_commands.describe(count="จำนวนครั้ง (1-30)")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def spam_slash(interaction: discord.Interaction, count: int = 5):
    await interaction.response.defer(ephemeral=True)
    await single_flood(interaction, EMOJI_PAYLOAD, count)

@tree.command(name="ส่งอิโมจิ", description="ส่ง emoji ที่ต้องการซ้ำๆ")
@app_commands.describe(emoji="emoji เช่น 😈🔥💀", count="จำนวนครั้ง (1-30)")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def send_emoji(interaction: discord.Interaction, emoji: str, count: int = 5):
    await interaction.response.defer(ephemeral=True)
    payload = (emoji * (2000 // max(len(emoji), 1)))[:2000]
    await single_flood(interaction, payload, count)

@tree.command(name="ส่งข้อความ", description="ส่งข้อความที่ต้องการซ้ำๆ")
@app_commands.describe(ข้อความ="ข้อความที่จะส่ง", count="จำนวนครั้ง (1-30)")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def send_msg(interaction: discord.Interaction, ข้อความ: str, count: int = 5):
    await interaction.response.defer(ephemeral=True)
    await single_flood(interaction, ข้อความ[:2000], count)

@tree.command(name="ส่งสแปมด่า", description="สวัสดีชาวโลกพี่มาแล้วยิงยับๆ")
@app_commands.describe(count="จำนวนครั้ง (1-30)")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def send_spam_da(interaction: discord.Interaction, count: int = 5):
    await interaction.response.defer(ephemeral=True)
    await single_flood(interaction, SPAM_DA_TEXT, count)

@tree.command(name="สแปมลูป", description="ส่ง emoji วนไปเรื่อยๆ จนกว่าจะ /หยุด")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def spam_loop(interaction: discord.Interaction):
    cid = interaction.channel_id
    if active_loops.get(cid):
        await interaction.response.send_message("⚠️ loop ทำงานอยู่แล้ว — /หยุด ก่อน", ephemeral=True)
        return
    await interaction.response.send_message("🔁 loop เริ่มแล้ว — /หยุด เพื่อหยุด", ephemeral=True)
    asyncio.create_task(loop_flood(cid, EMOJI_PAYLOAD))

@tree.command(name="สแปมข้อความลูป", description="ส่งข้อความที่กำหนดวนไปเรื่อยๆ")
@app_commands.describe(ข้อความ="ข้อความที่จะวนส่ง")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def spam_msg_loop(interaction: discord.Interaction, ข้อความ: str):
    cid = interaction.channel_id
    if active_loops.get(cid):
        await interaction.response.send_message("⚠️ loop ทำงานอยู่แล้ว", ephemeral=True)
        return
    await interaction.response.send_message("🔁 loop เริ่มแล้ว — /หยุด เพื่อหยุด", ephemeral=True)
    asyncio.create_task(loop_flood(cid, ข้อความ[:2000]))

@tree.command(name="หยุด", description="หยุด loop spam ใน channel นี้")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def stop_loop(interaction: discord.Interaction):
    cid = interaction.channel_id
    if active_loops.get(cid):
        active_loops[cid] = False
        await interaction.response.send_message("🛑 กำลังหยุด...", ephemeral=True)
    else:
        await interaction.response.send_message("❌ ไม่มี loop ทำงานอยู่", ephemeral=True)

# ══════════════════════════════════════════
#  prefix fallback
# ══════════════════════════════════════════
@bot.command(name="spam")
@commands.has_permissions(send_messages=True)
async def spam_prefix(ctx, count: int = 5):
    count = max(1, min(count, 30))
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass
    for _ in range(count):
        try:
            await ctx.send(EMOJI_PAYLOAD)
            await asyncio.sleep(0.4)
        except discord.HTTPException as e:
            if e.status == 429:
                retry = float(e.response.headers.get("Retry-After", 1.0))
                await asyncio.sleep(retry)
            else:
                break

@bot.command(name="stop")
@commands.has_permissions(administrator=True)
async def stop_cmd(ctx):
    await ctx.send("🔴 shutting down")
    await bot.close()

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ no permission", delete_after=3)
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ ใส่ตัวเลข เช่น `!spam 10`", delete_after=3)

if __name__ == "__main__":
    if TOKEN == "YOUR_BOT_TOKEN":
        raise SystemExit("[!] ใส่ TOKEN ก่อน")
    bot.run(TOKEN, log_handler=None)