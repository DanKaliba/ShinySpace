# Co v analýze zatím chybí

Seřazeno podle toho, kolik by to podle mě přineslo pro rozhodování příští kampaně.

## Data jsou volně k dispozici, jde jen o práci

1. ~~**Demografie po okrscích (SLDB 2021).**~~ *Hotovo v sekci Demografie, s omezením: věk a byty z 1km gridu, vzdělání jen po MČ. Vzdělání po okrscích by vyžadovalo data ČSÚ za ZSJ nebo za sčítací obvody (na objednávku).*
2. **Dělení hlasů mezi MČ a magistrátem.** Stejní voliči ve stejný den: kolik voličů pirátské magistrátní kandidátky nevolilo Piráty v MČ a naopak, po okrscích. Ukáže, kde je „značka“ silnější než místní tým.
3. **Preferenční hlasy na magistrát po okrscích Prahy 5.** Kteří pražští lídři táhli na Praze 5 a kde.
4. **Sněmovna 2025 → komunál 2026 jako přesun voličů.** Stejný model jako Sankey, jen s PS 2025 na vstupu. Kolik lidí, kteří Piráty volili před rokem, letos nepřišlo vůbec.
5. **Účast jako samostatný cíl.** Kde stoupla účast a kdo z ní těžil (STAN?). Pirátští voliči se podle povolebních průzkumů rozhodují pozdě, takže mobilizace v posledním týdnu je klíčová.
6. **2. kolo Senátu (16.–17. 10.).** Doplnit, jakmile budou data: kam šli voliči Šarapatky mezi Láskou a Sáblíkem.
7. **Nová výstavba.** Okrsky, kde od roku 2022 nejvíc přibylo voličů (Smíchov City, Waltrovka, Barrandov), jsou noví obyvatelé bez vazby na místní politiku. Jak tam volili?

## Potřeba interní data strany

8. **Dosah akcí, ne jen počet.** Počet rozdaných letáků, rozhovorů a podpisů pod peticí po akcích. Bez toho analýza akcí měří jen to, kde akce byly.
9. **Online kampaň.** Geografie výdajů na reklamu a dosah na sociálních sítích, pokud jsou k dispozici po PSČ.
10. **Kontakty z petic** (Barrandov, školky): kolik lidí z okrsků, kde se podepisovalo.

## Metodické rozšíření

11. **Lepší ekologická inference** (King, hierarchický bayesovský model nebo RxC metoda). Dala by užší intervaly než Goodmanova regrese, ale bez scipy nebo PyMC to tady nejde.
12. **Monte Carlo mandátů.** Jak často by při náhodném kolísání hlasů o ±1 % Piráti dostali 4. mandát. Dnes víme jen bodově: chybělo 825 hlasů.
13. **Srovnání s podobnými městskými částmi** (Praha 6, 7, 10). Liší se Praha 5 od trendu víc, než je náhoda?
