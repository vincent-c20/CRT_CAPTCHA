# CRT Captcha 🟢

Un générateur de CAPTCHA visuel inspiré des anciens écrans CRT, basé sur une technique de **dissimulation temporelle du texte dans du bruit**.

L'objectif est de créer un CAPTCHA qui exploite une capacité naturelle de la vision humaine : **l'intégration des informations dans le temps**. Le texte caché est invisible ou très difficile à lire sur une image fixe, mais apparaît lorsqu'on observe l'animation.

---

## ✨ Aperçu

Le rendu ressemble à un écran phosphore :

- fond noir
- pixels vert pâle
- bruit aléatoire
- effet rétro CRT
- texte caché qui apparaît progressivement

Exemple :

```
▒ ░ ▒ ░ ▒ ░ ▒ ░ ▒
  bruit + signal caché
▒ ░ ▒ ░ ▒ ░ ▒ ░ ▒
```

Un humain voit un mot après quelques instants, alors qu'une analyse image simple ne voit qu'un nuage de pixels.

---

## 🧠 Principe

Le CAPTCHA repose sur une séparation du signal :

1. Le texte est converti en pixels.
2. Les pixels du texte sont mélangés aléatoirement.
3. Ils sont divisés en plusieurs tranches.
4. Chaque frame affiche :
   - une partie du texte réel
   - une quantité équivalente de bruit aléatoire
5. Les frames changent rapidement.

Le cerveau humain accumule les informations :

```
Frame 1 :  █  ·  ·  █  ·
Frame 2 :  ·  █  █  ·  ·
Frame 3 :  █  ·  █  ·  █
Frame 4 :  ·  █  ·  █  ·

Résultat perçu :
        TEXTE
```

---

## 🚀 Utilisation

Aucune dépendance.

Clone le projet :

```bash
git clone https://github.com/VOTRE_USERNAME/crt-captcha.git
cd crt-captcha
```

Ouvre simplement :

```bash
index.html
```

dans un navigateur.

---

## ⚙️ Configuration

Les paramètres principaux :

```javascript
const ORIG_W = 168;
const ORIG_H = 42;

const SCALE = 8;

const N_SLICES = 4;

const FRAME_MS = 20;
```

### ORIG_W / ORIG_H

Résolution interne du CAPTCHA.

Plus la résolution est grande :
- plus les messages peuvent être longs
- plus la reconstruction est difficile

---

### SCALE

Facteur d'agrandissement des pixels.

Exemple :

```
pixel source :
■

avec SCALE = 8 :

■■■■■■■■
■■■■■■■■
■■■■■■■■
■■■■■■■■
```

---

### N_SLICES

Nombre de couches temporelles.

Valeurs typiques :

| valeur | effet |
|-|-|
| 2 | très visible |
| 4 | équilibré |
| 8 | plus difficile |

---

### FRAME_MS

Vitesse d'animation.

20ms correspond à environ :

```
50 FPS
```

---

## 🛠 Génération d'un nouveau CAPTCHA

Le texte est stocké sous forme de coordonnées :

```javascript
const DIGIT_PIXELS = [
  [x, y],
  [x, y],
  ...
];
```

Chaque paire correspond à un pixel allumé.

Pour générer un nouveau message :

1. Convertir le texte en bitmap.
2. Extraire les pixels actifs.
3. Remplacer `DIGIT_PIXELS`.

---

## 🔒 Pourquoi c'est difficile à lire automatiquement ?

Une frame seule contient :

- une fraction du texte
- beaucoup de bruit
- aucune information complète

Un OCR classique reçoit donc :

```
signal faible + bruit fort
```

Alors que l'utilisateur humain bénéficie de :

```
plusieurs frames + mémoire visuelle
```

---

## ⚠️ Limitations

Ce projet est expérimental.

Il ne remplace pas un CAPTCHA industriel :

- pas de validation serveur
- pas de protection anti-rejeu
- texte exposé dans le code source
- vulnérable à une analyse vidéo complète

Il s'agit surtout d'une expérience sur la perception visuelle.

---

## 📜 Licence

MIT License

Libre d'utilisation, modification et redistribution.

---

## 💡 Idée

Ce projet explore une question :

> Peut-on cacher une information à une machine tout en la laissant évidente pour un humain ?
