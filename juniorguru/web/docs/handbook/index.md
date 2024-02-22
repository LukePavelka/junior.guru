---
title: Příručka pro juniory
emoji: 🗺️
thumbnail_badge: zdarma
description: Obsáhlá příručka pro všechny, kdo se chtějí naučit programovat a najít si práci v oboru.
template: main_handbook.html
---

{% from 'macros.html' import lead, note, blockquote_avatar with context %}

# Příručka pro juniory

{% call lead() %}
  Uvažuješ o programování? Láká tě zjistit, jak automatizovat část své práce? Přemýšlíš nad kariérní změnou do IT, ale nevíš jak na to? Studuješ informatiku a zajímá tě, co dál?
{% endcall %}

## Cesta juniora

Na základě reálných zkušeností mnohých začátečníků jsme v [klubu](../club.md) sestavili **osvědčenou cestu juniora**, která má deset fází. Možná existují i jiné cesty, ale tato **úspěšně zafungovala pro spoustu různých lidí**, a proto ji lze obecně doporučit.

**Ujasni si, co už umíš a co je tvým cílem.** Jednak ti to pomůže uvědomit si, co tě ještě čeká a co nesmíš vynechat, jednak zjistíš, které části příručky pro tebe budou nejpřínosnější.

Pokud o IT teprve přemýšlíš (fáze 0), budou pro tebe zajímavé jiné rady, než pokud už máš za sebou nějaký kurz (fáze 2 až 3). A jestli tě programování zajímá proto, že chceš automatizovat zalévání rajčat na zahradě (fáze 3), nemusí tě zajímat kapitoly o shánění práce v oboru (fáze 4 až 10).

0. Občas mě napadne, že by nemusela být úplná blbost učit se programovat: [Motivace](motivation.md)
{: value=0 }
1. Nezávazně zkouším všechno možné, nebo začínám s jednou věcí, o které si myslím, že ji chci dělat: [Základy](motivation.md), [Vybírání kurzu](course.md), [Řešení problémů](help.md)
2. Učím se to, co si myslím, že chci dělat. Samostatně, ve škole, v kurzu: [Základy](motivation.md), [Vybírání kurzu](course.md), [Řešení problémů](help.md), [První praxe](practice.md), [Git a GitHub](git.md)
3. Pracuju na projektech: [První praxe](practice.md), [Git a GitHub](git.md)
4. Připravuji se na hledání práce, ladím CV apod.: [Životopis](cv.md), [LinkedIn](linkedin.md), [Hledání práce](candidate.md)
5. Hledám práci: [Hledání práce](candidate.md)
6. Mám nalezenou nebo domluvenou práci a nastupuji v budoucnu.
7. Zkušební doba v první práci v oboru.
8. Pracuji po zkušební době.
9. Mám 1 až 2 roky komerční praxe.
10. Už nejsem junior.

Ne každou fázi se zatím povedlo pokrýt kapitolami v příručce, ale se všemi pomáháme a všechny diskutujeme ve zdejším [klubu](../club.md).


<!-- {#

## Jak funguje tato příručka

- Kdo ji píše
- Proč ji píše
- message na úvodní stránce příručky - články versus content, dnes už nikdo content nedělá, chtějí to spláchnout clankem, ne udržovat nějaké informace (Czechitas, Engeto)

fáze https://discord.com/channels/769966886598737931/788826407412170752/904981964208087070

nela https://github.com/NelliaS/development-timeline

https://www.freecodecamp.org/news/what-is-web-development-how-to-become-a-web-developer-career-path/

https://twitter.com/jzunigacoayla/status/1380694681911226373

https://blog.lewagon.com/skills/programming-language-to-learn/

https://roadmap.sh/

https://codeburst.io/the-2018-web-developer-roadmap-826b1b806e8d

https://twitter.com/ladybugpodcast/status/1247051343212281856

Front-end Developer Handbook 2019
https://frontendmasters.com/guides/front-end-handbook/2019/

How to Learn to Code & Get a Developer Job [Full Book]
https://www.freecodecamp.org/news/learn-to-code-book/#500-word-executive-summary

https://learntocodewith.me/

https://www.pythondiscord.com/resources/

--- https://discord.com/channels/769966886598737931/788826407412170752/904981964208087070
**Fáze juniora.**

Skoro u každýho kroku je možno se zaseknout a nepřejít dál.
Každej krok má svoje úskalí.

0️⃣ **občas mě něco jako učit se programovat napadne**
úskalí: nezačnu nebo začnu, ale první zkušenost je špatná

1️⃣ **nezávazně zkouším všechno možné nebo začínám s jednou věcí, o které si myslím, že ji chci dělat**
úskalí: nemůžu se rozhodnout mezi technologiemi či oblastmi

2️⃣ **učím se samostatně / v kurzu to, co si myslím, že chci dělat**
úskalí: sám nevím kam až / kurz zas nemusí být dostatečný nebo kvalitní / nedaří se mi najít si dost času se tomu věnovat

3️⃣ **pracuju na projektech**
úskalí: nevím jak začít / nevím jaký projekt / nedám projekt (ani průběžně) ke zhodnocení / špatně odhadnutý rozsah projektu

4️⃣ **připravuju se na hledání práce (CV apod.)**
úskalí: neodvažuju se do téhle fáze přejít, nevím co se v IT očekává nebo dokonce nemám moc zkušeností s prací celkově / neumím sám sebe „prodávat“, mám problém napsat pozitiva do CV

5️⃣ **hledám práci**
úskalí: nemám dostatečnou výdrž / nemám dostatečnou finanční rezervu / odradí mě první neúspěchy / vezmu cokoli i když je to něco jiného, než jsem chtěl dělat (někdy ok, někdy problém)

6️⃣ **mám nalezenou/domluvenou práci a nastupuju v budoucnu**
úskalí: nezačnu se vůbec sám učit technologii, kterou ve firmě používají  nebo to s tím naopak místo odpočinku přeženu

7️⃣ **zkušební doba v první práci**
úskalí: málo se ptám seniora a tím se málo učím / není k dispozici senior / zůstanu ve firmě i když je to tam zjevně špatný

8️⃣ **pracuju (po zkušební době)**
úskalí: přestanu se rozvíjet a učit, nedostávám pokročilejší úkoly

9️⃣ **mám 1-2 roky praxe**
úskalí: to co v 8️⃣ + neřeknu si o větší peníze, přestože mám na trhu o dost vyšší cenu než na začátku

🔟 už nejsem „junior“
---


--- https://discord.com/channels/769966886598737931/788832177135026197/894840146845925427
https://www.codecademy.com/resources/docs

Blog post k tomu https://www.codecademy.com/resources/blog/introducing-docs/

Samozřejmě jsou jiné existující zdroje, ale tady je to hodně stručně, takže to začátečníci asi ocení.
---


--- https://discord.com/channels/769966886598737931/788832177135026197/1061972910488703036
Spíše motivační četba, ale pěkný článek. Něco jako příručka junior.guru ale od freeCodeCamp 🙂
https://www.freecodecamp.org/news/learn-to-code-book/#500-word-executive-summary
---


--- https://discord.com/channels/769966886598737931/788826407412170752/1055146186413187102
Doufal jsem, že sem taky budu moct jednou napsat, že jsem konečně v klubu a našel jsem práci. A stalo se to ! Od února se budu podílet na softwaru v automobilech v Pythonu. 🤩

Od začátku utekly dva roky, kolik jsem oslovil firem přesně nevím, ale mohlo to být kolem dvaceti. Hlavně bych ale chtěl říct, že na začátku není důležité někam spěchat - což se mi také stalo. Pak jsem si uvědomil, že stihnout to za pár měsíců souběžně s prací a rodinou je blbost. A tak jsem v klidnějším tempu pokračoval k cíli.

Pár slov a odkazů k cestě, na začátku za mě nejlepší start na https://www.umimeinformatiku.cz/programovani-v-pythonu , to mi pomohlo nejvíc a je to hlavně zábavnou formou příkladů. Pak jsem si vybral projekt od https://www.techwithtim.net/ , který má super tutorialy na Youtube a zakončil jsem to projektem s Corey Schafer také na Youtube, nicméně ty už jsou pro pokročilejší.

U pohovoru také dost pomohl GitHub, který doporučuji si založit hned první den. Jednak mě motivoval ten kalendář příspěvků udělat něco pokud možno alespoň každý druhý den. A poté je vidět jak dlouho už se člověk tématem zabývá. 🙂

Hodně zdaru, sil a velký dík Honzovi, že to tu založil a spravuje <:dk:842727526736068609> 🥳
---


--- https://discord.com/channels/769966886598737931/788826407412170752/1054800375703683113
Níže založím vlákno s malým shrnutím mého hledání práce, které jsem teď završil přijetím nabídky na pozici Java vývojáře s nástupem v únoru. Přidám pár postřehů o tom, co bych udělal stejně/jinak, kdybych si znovu hledal práci. Taky zmíním jména pár firem, které na mě působily velmi dobře, nebo naopak velmi špatně, a proč. Celé je to založené na mých zkušenostech podpořenými zkušenostmi z práce v IT recruitmentu. Takže všechno můj názor, i když to místy napíšu jako “poučku s absolutní pravdou” nebo tak něco 🙂
---




#} -->
