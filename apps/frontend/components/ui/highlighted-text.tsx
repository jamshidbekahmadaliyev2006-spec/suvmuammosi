"use client";

import React, { useMemo } from "react";

interface HighlightedTextProps {
  text?: string | null;
  keywords?: string[];
  className?: string;
  markClassName?: string;
}

const CYR_TO_LAT: Record<string, string> = {
  а: "a", б: "b", в: "v", г: "g", д: "d", е: "e", ё: "yo",
  ж: "j", з: "z", и: "i", й: "y", к: "k", л: "l", м: "m",
  н: "n", о: "o", п: "p", р: "r", с: "s", т: "t", у: "u",
  ф: "f", х: "x", ц: "ts", ч: "ch", sh: "sh", щ: "sh",
  ъ: "'", ь: "", э: "e", ю: "yu", я: "ya", ў: "o'", қ: "q",
  ғ: "g'", ҳ: "h",
};

const LAT_TO_CYR: Record<string, string> = {
  a: "а", b: "б", v: "в", g: "г", d: "д", e: "е", yo: "ё",
  j: "ж", z: "з", i: "и", y: "й", k: "к", l: "л", м: "м",
  n: "н", o: "о", p: "п", r: "р", s: "с", t: "т", u: "у",
  f: "ф", x: "х", ts: "ц", ch: "ч", sh: "ш", yu: "ю", ya: "я",
  "o'": "ў", q: "қ", "g'": "ғ", h: "ҳ",
};

function transliterateCyrToLat(str: string): string {
  let res = "";
  for (let i = 0; i < str.length; i++) {
    const ch = str[i].toLowerCase();
    res += CYR_TO_LAT[ch] || ch;
  }
  return res;
}

function transliterateLatToCyr(str: string): string {
  let s = str.toLowerCase();
  s = s
    .replace(/o['’‘`]/g, "ў")
    .replace(/g['’‘`]/g, "ғ")
    .replace(/sh/g, "ш")
    .replace(/ch/g, "ч")
    .replace(/yo/g, "ё")
    .replace(/yu/g, "ю")
    .replace(/ya/g, "я")
    .replace(/ts/g, "ц");
  let res = "";
  for (let i = 0; i < s.length; i++) {
    res += LAT_TO_CYR[s[i]] || s[i];
  }
  return res;
}

// Kalit so'zlarning ko'p so'zli juftliklari va mavzuli ma'nodosh variantlari
const CONCEPT_DICTIONARY: { keys: string[]; phrases: string[] }[] = [
  {
    keys: ["ёнғин", "yongin", "yong'in", "ёниб", "yonib", "пожар", "олов", "olov"],
    phrases: [
      "ёнғин чиққан", "ёнғин чиқди", "ёнғин содир бўлди", "ёнғин содир", "ёнғин бўлди",
      "ёниб кетди", "ёниб кетипти", "ёниб кетган", "тириклайин ёниб", "олов ичида",
      "yong'in chiqqan", "yongin chiqqan", "yong'in chiqdi", "yongin chiqdi", "yong'in sodir bo'ldi",
      "yonib ketdi", "yonib ketipti", "yonib ketgan", "tiriklayin yonib", "olov ichida",
      "пожар произошел", "случился пожар", "вспыхнул пожар", "возгорание произошло", "пожар",
    ],
  },
  {
    keys: ["ёмғир", "yomgir", "yomg'ir", "дожд", "ливн"],
    phrases: [
      "ёмғир суви", "ёмғир сувлари", "ёмғир сувидан", "ёмғирнинг суви",
      "ёмғир кучли ёғмоқда", "кучли ёмғир", "ёмғир ёғиб",
      "дождевая вода", "дождевые воды", "дождевой воды", "ливневая вода", "ливневые воды", "сильный дождь", "ливень",
      "yomg'ir suvi", "yomgir suvi", "yomg'ir suvlari", "yomgir suvlari", "yomg'ir suvidan", "yomg'ir kuchli yog'moqda", "kuchli yomg'ir",
    ],
  },
  {
    keys: ["затоп", "zatop"],
    phrases: ["затоп", "затопило", "подтопило", "подтопление", "zatop"],
  },
  {
    keys: ["жижа", "jija"],
    phrases: ["жижа", "jija"],
  },
  {
    keys: ["тошди", "тошган", "тошиб", "босди", "босган", "toshdi", "toshgan", "toshib", "bosdi", "bosgan"],
    phrases: [
      "сув тошди", "сув тошган", "сув тошиб", "сув тошиб кетмоқда", "сув босди", "сув босган",
      "канал тошди", "канал тошган", "канал тошиб", "канал тошиб кетди", "каналда сув тошди",
      "ариқлардан сув тошган", "йўлга сув тошган", "мост тагида сув", "тратуарга сув", "тротуарга сув",
      "вода затопила", "затопление водой", "подтопило водой",
      "suv toshdi", "suv toshgan", "suv toshib", "suv bosdi", "suv bosgan", "kanal toshdi",
    ],
  },
  {
    keys: ["чиқинди", "аҳлат", "мусор", "chiqindi", "axlat", "musor"],
    phrases: [
      "чиқинди ташланди", "чиқинди ташланмоқда", "йиғилган аҳлат", "мусор ташланди", "ахлат ташланди",
      "каналда чиқинди", "каналга чиқинди", "ариққа чиқинди", "сброс мусора",
      "chiqindi tashlandi", "chiqindi tashlanmoqda", "musor tashlandi", "axlat tashlandi",
    ],
  },
  {
    keys: ["труба", "қувур", "truba", "quvur"],
    phrases: [
      "труба тиқилиб", "труба тиқилиб қолган", "қувур тиқилиб", "қувур тиқилиб қолган",
      "труба ёрилди", "қувур ёрилди", "труба тешилди", "қувур тешилди", "прорыв трубы", "засор трубы",
      "truba tiqilib", "quvur tiqilib", "truba yorildi", "quvur yorildi",
    ],
  },
  {
    keys: ["канализация", "конализация", "оқава", "kanalizatsiya", "oqava"],
    phrases: [
      "канализация тошмоқда", "канализация тошди", "конализация тошмоқда",
      "оқава сув ташланмоқда", "оқава сув", "канализация суви", "разлив канализации",
      "kanalizatsiya toshmoqda", "oqava suv",
    ],
  },
  {
    keys: ["сув йўқ", "suv yoq", "suv yo'q"],
    phrases: ["каналда сув йўқ", "сув йўқ", "сув йўқлиги", "suv yo'q", "suv yoq", "kanalda suv yo'q"],
  },
  {
    keys: ["венеция", "venetsiya"],
    phrases: ["венеция бўлиб тошмоқда", "венеция бўлиб", "венецияга айланди", "венеция", "venetsiya"],
  },
  {
    keys: ["без осадков", "yogingarchiliksiz"],
    phrases: ["без осадков", "yog'ingarchiliksiz", "ёғингарчиликсиз"],
  },
  {
    keys: ["чақмоқ", "chaqmoq", "молния", "lightning"],
    phrases: [
      "чақмоқ чақиши", "чақмоқ уриши", "чақмоқ урди", "чақмоқ чақди", "молния ударила", "удар молнии",
      "chaqmoq chaqishi", "chaqmoq urishi", "chaqmoq urdi", "chaqmoq chaqdi", "lightning strike",
    ],
  },
];

const STOP_WORDS = new Set([
  "va", "ham", "bilan", "uchun", "yoki", "esa", "ekan", "deb", "dep", "biri",
  "lekin", "ammo", "shuningdek", "haqida", "bu", "shu", "har", "oz", "o'z",
  "juda", "bo'yicha", "boyicha", "tomonidan",
]);

// Global regex keshi
const REGEX_CACHE = new Map<string, { regex: RegExp; testRegex: RegExp; terms: Set<string> }>();

/**
 * Xabarlar va sarlavhalardagi kalit so'zlarni JUFTI BILAN (yonma-yon) aniqlab,
 * ularni ko'rinarli qilib OTMETKA QILIB TAGIGA CHIZIB (underline & highlight) ko'rsatish komponenti.
 * Bitta umumiy so'zni (masalan, alohida "suv" yoki alohida "chiqqan") o'zicha ajratib olib chizmaydi!
 */
export function HighlightedText({
  text,
  keywords = [],
  className = "",
  markClassName = "",
}: HighlightedTextProps) {
  const cacheKey = keywords.join("|");

  const compiled = useMemo(() => {
    if (!keywords || keywords.length === 0) return null;

    if (REGEX_CACHE.has(cacheKey)) {
      return REGEX_CACHE.get(cacheKey)!;
    }

    const set = new Set<string>();

    keywords.forEach((raw) => {
      if (!raw) return;
      const cleanRaw = raw.replace(/[.,!?:;\"'()\[\]{}]/g, " ").trim();
      if (!cleanRaw) return;

      const lowRaw = cleanRaw.toLowerCase();
      const rawNoQuotes = lowRaw.replace(/['’‘`]/g, "");
      const words = lowRaw.split(/\s+/).filter((w) => w.length >= 2 && !STOP_WORDS.has(w));

      if (words.length === 0) return;

      // 1. Agar kalit 1 ta so'zdan iborat bo'lsa (masalan: "Затоп", "Жижа")
      if (words.length === 1) {
        const single = words[0];
        set.add(single);
        const lat = transliterateCyrToLat(single);
        if (lat) set.add(lat);
        const cyr = transliterateLatToCyr(single);
        if (cyr) set.add(cyr);
      } else {
        // 2. Agar kalit 2 yoki undan ko'p so'zdan iborat bo'lsa (JUFTI BILAN, YONMA-YON)
        set.add(lowRaw);
        const fullLat = transliterateCyrToLat(lowRaw);
        if (fullLat) set.add(fullLat);
        const fullCyr = transliterateLatToCyr(lowRaw);
        if (fullCyr) set.add(fullCyr);

        // Qo'shni so'zlar juftligini qo'shish
        for (let i = 0; i < words.length - 1; i++) {
          const pair = `${words[i]} ${words[i + 1]}`;
          set.add(pair);
          const pairLat = transliterateCyrToLat(pair);
          if (pairLat) set.add(pairLat);
          const pairCyr = transliterateLatToCyr(pair);
          if (pairCyr) set.add(pairCyr);
        }
      }

      // 3. Mavzuli konsept lug'atidan kengaytirish (sinonimlar va imlo o'xshashlari)
      for (const concept of CONCEPT_DICTIONARY) {
        const matchesConcept = concept.keys.some((k) => {
          const kClean = k.replace(/['’‘`]/g, "").toLowerCase();
          return lowRaw.includes(k) || rawNoQuotes.includes(kClean);
        });

        if (matchesConcept) {
          concept.phrases.forEach((phrase) => {
            const pLow = phrase.toLowerCase();
            set.add(pLow);
            const pLat = transliterateCyrToLat(pLow);
            if (pLat) set.add(pLat);
            const pCyr = transliterateLatToCyr(pLow);
            if (pCyr) set.add(pCyr);
          });
        }
      }
    });

    if (set.size === 0) return null;

    // Eng uzun iboralar oldin mos kelishi uchun saralash
    const sorted = Array.from(set).sort((a, b) => b.length - a.length);
    const escaped = sorted.map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));

    const pattern = `(${escaped.join("|")})`;
    const regex = new RegExp(pattern, "gi");
    const testRegex = new RegExp(`^(?:${escaped.join("|")})$`, "i");

    const result = { regex, testRegex, terms: set };
    if (REGEX_CACHE.size > 25) {
      REGEX_CACHE.clear();
    }
    REGEX_CACHE.set(cacheKey, result);
    return result;
  }, [keywords, cacheKey]);

  if (!text) return null;

  if (!compiled) {
    return <span className={className}>{text}</span>;
  }

  const parts = text.split(compiled.regex);

  // Otmetka qilib, tagiga aniq chizib ko'rsatish stili
  const defaultMarkClass =
    "bg-amber-100/95 dark:bg-amber-950/80 text-amber-950 dark:text-amber-100 font-extrabold underline decoration-amber-500 decoration-[2.5px] underline-offset-4 px-1 py-0.5 rounded shadow-2xs inline-block transition-transform hover:scale-105";

  return (
    <span className={`whitespace-pre-line leading-relaxed ${className}`}>
      {parts.map((part, index) => {
        if (!part) return null;
        const isMatch = compiled.testRegex.test(part.trim());

        if (isMatch) {
          return (
            <mark
              key={index}
              className={markClassName || defaultMarkClass}
              title={`Aniqlangan kalit so'z: «${part}»`}
            >
              {part}
            </mark>
          );
        }

        return <span key={index}>{part}</span>;
      })}
    </span>
  );
}
