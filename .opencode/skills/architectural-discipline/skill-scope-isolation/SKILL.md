---
name: skill-scope-isolation
description: "KARDYNALNA ZASADA struktury skilli: kazdy skill opisuje tylko i wylacznie swoj koncept/ temat i nie posiada zadnej wiedzy o innych konceptach ani o niczym, co go bezposrednio nie dotyczy. Z zadnego skill-a nie mozna wyprowadzic zadnych wnioskow o innym skille. Uzywaj przy tworzeniu, aktualizacji i review plikow SKILL.md."
---

# Skill Scope Isolation — jeden skill = jeden koncept

## 1. Fundamentalna regula

Kazdy skill opisuje **tylko i wylacznie swoj koncept** — swoja odpowiedzialnosc,
wejscia/wyjscia, przeplyw, kontrakt i wzorce wlasne.

Skill **nie moze nic wiedziec** o innych tematach, konceptach ani o niczym, co
go bezposrednio nie dotyczy.

**Z zadnego skill-a nie mozna wyprowadzic zadnych wnioskow o innym skille.**
Cala wiedza o koncepcie B zyje wylacznie w skille B i tylko tam. Skill A nie
zawiera zadnych wlasciwosci, regu ani szczegolow dotyczacych B.

## 2. Co moze zawierac skill

- definicje i odpowiedzialnosci **wlasnego** konceptu;
- wejscia i wyjscia **wlasnego** konceptu;
- przeplyw i wzorce **wlasnego** konceptu;
- kontrakt i dowod implementacji **wlasnego** konceptu;
- minimalne wskazanie granicy, gdy jest czescia wlasnej definicji: jedna linia
  "to nie jest X" — bez zadnych szczegolow o X, bez implikacji operacyjnych o X.

## 3. Czego skill nie moze zawierac

- szczegolow, regu, przeplywu ani implementacji **innego** konceptu;
- tresci, z ktorej mozna wyprowadzic wniosek o innym skille;
- dublowania wiedzy, ktora posiada inny skill;
- odnosnikow zawierajacych tresc (referencja ma byc tylko wskazaniem nazwy/modulu,
  nigdy nosnikiem tresci).

## 4. Referencje

Wolno wskazac, ze koncept B definiuje osobny skill: `patrz <nazwa-skilla>`.
Referencja jest **wskazaniem**, nie trescia. Nie wolno cytowac, streszczac ani
opisywac B w A.

## 5. Przeglad i naprawa

Gdy podczas review trec A opisuje koncept B:

1. okresl wlasciciela tematu (skill, ktorego konceptem jest B);
2. **wyprowadz** niepasujaca tresc do skilla B;
3. w A pozostaw wyrazne wskazanie: `szczegoly w <nazwa-skilla>`;
4. nie usuwaj tresci z repo — przenies ja do wlasciciela;
5. po przeniesieniu nie dubluj jej w A.

## 6. Kryterium zadowolenia

Przeglad dowolnego fragmentu skilla A nie pozwala wywnioskowac nic o koncepcie B.
Kazdy fragment A odpowiada na pytanie: "jakiej prawdy o **wlasnym** koncepcie
uczy czytelnika?"