import discord
from discord.ext import commands
import requests
from PIL import Image
from io import BytesIO
from datetime import datetime
import os

# --- CONFIGURAZIONE ---
ADMIN_IDS = [1171135456306536450, 924641550133248000]
# ----------------------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

vittorie = {}

def get_image_bytes(url):
    response = requests.get(url)
    return Image.open(BytesIO(response.content)).resize((256, 256))

class hView(discord.ui.View):
    def __init__(self, p1, p2, embed):
        super().__init__(timeout=120)
        self.p1 = p1
        self.p2 = p2
        self.embed = embed
        self.rematch_button = discord.ui.Button(label="Rematch", style=discord.ButtonStyle.primary, emoji="🔄", row=1)
        self.rematch_button.callback = self.rematch_callback
        self.rematch_button.disabled = True
        self.add_item(self.rematch_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in ADMIN_IDS:
            await interaction.response.send_message("❌ Solo gli owner possono usare i bottoni!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Win P1", style=discord.ButtonStyle.green)
    async def win_p1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.end_match(interaction, self.p1)

    @discord.ui.button(label="Win P2", style=discord.ButtonStyle.green)
    async def win_p2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.end_match(interaction, self.p2)

    async def end_match(self, interaction, winner):
        vittorie[winner.display_name] = vittorie.get(winner.display_name, 0) + 1
        self.embed.title = "🏆 MATCH CONCLUDED"
        self.embed.description = f"The winner is **{winner.mention}**!\n\n📊 {winner.display_name} has won {vittorie[winner.display_name]} times."
        self.embed.color = discord.Color.green()
        
        url_win = winner.avatar.url if winner.avatar else winner.default_avatar.url
        winner_img = get_image_bytes(url_win)
        buffer = BytesIO()
        winner_img.save(buffer, format='PNG')
        buffer.seek(0)
        file = discord.File(buffer, filename="winner.png")
        self.embed.set_image(url="attachment://winner.png")
        
        for child in self.children: child.disabled = True
        self.rematch_button.disabled = False
        
        await interaction.followup.edit_message(message_id=interaction.message.id, embed=self.embed, view=self, attachments=[file])

    async def rematch_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await show_match(interaction.channel, self.p1, self.p2)

async def show_match(channel, p1, p2):
    url1 = p1.avatar.url if p1.avatar else p1.default_avatar.url
    url2 = p2.avatar.url if p2.avatar else p2.default_avatar.url
    img1, img2 = get_image_bytes(url1), get_image_bytes(url2)
    collage = Image.new('RGB', (512, 256))
    collage.paste(img1, (0, 0)); collage.paste(img2, (256, 0))
    buffer = BytesIO()
    collage.save(buffer, format='PNG'); buffer.seek(0)
    file = discord.File(buffer, filename="match.png")
    
    embed = discord.Embed(title="⚔️ 1v1 MATCH", description=f"{p1.mention} VS {p2.mention}", color=discord.Color.gold())
    embed.add_field(name="Player 1", value=f"{p1.mention}", inline=True)
    embed.add_field(name="Player 2", value=f"{p2.mention}", inline=True)
    embed.set_image(url="attachment://match.png")
    embed.set_footer(text=f"Match created on {datetime.now().strftime('%d/%m/%Y - %H:%M')}")
    
    await channel.send(embed=embed, file=file, view=hView(p1, p2, embed))

@bot.command()
async def match(ctx, p1: discord.Member, p2: discord.Member):
    if ctx.author.id not in ADMIN_IDS: return
    await show_match(ctx.channel, p1, p2)

bot.run(os.environ['TOKEN'])
      
