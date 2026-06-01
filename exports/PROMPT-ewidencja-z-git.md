# Prompt: Ewidencja godzin z git log (opis pracy per dzień)

Skopiuj poniższy prompt do Claude Code / Coworka uruchomionego w danym repo.
Podmień **MIESIĄC** i **ROK** (oraz e-mail, jeśli chcesz filtrować po autorze).

---

```
Zrób ewidencję czasu pracy za <MIESIĄC ROK, np. maj 2026> na podstawie historii git w tym repozytorium.

Kroki:
1. Wyznacz zakres dat miesiąca (od 1. do ostatniego dnia).
2. Z `git log` w tym zakresie wyciągnij dla KAŻDEGO dnia z aktywnością:
   - commity (godzina + opis), posortowane chronologicznie,
   - zmienione pliki wraz z liczbą dodanych/usuniętych linii
     (`git log --numstat`), zagregowane per dzień.
3. Na podstawie commitów i zmienionych plików OPISZ co faktycznie zrobiono
   danego dnia — pełnymi zdaniami, rzeczowo (nie kopiuj samych nagłówków
   commitów). Wskaż główny rezultat dnia i skalę pracy (np. liczbę linii,
   nowe moduły, testy).
4. Zestaw wynik w tabeli: Data | Zakres godzin (pierwszy–ostatni commit) |
   Opis pracy.
5. Dodaj sekcję "Podsumowanie": liczba dni z aktywnością, łączna liczba
   commitów, lista kamieni milowych.
6. Oszacuj liczbę przepracowanych godzin dla każdego dnia na podstawie
   zakresu commitów, liczby zmienionych plików i charakteru pracy.
   WAŻNE: znaczniki czasu to momenty commitów — realna praca zaczyna się
   przed pierwszym commitem, więc traktuj zakres jako dolne oszacowanie.
   Zsumuj godziny w miesiącu.

Zasady:
- Bazuj WYŁĄCZNIE na danych z gita, nie zmyślaj zadań.
- Jeśli chcesz ograniczyć do moich commitów, filtruj autora: <twoj@email>.
- Zapisz wynik do pliku `exports/ewidencja-<miesiac>-<rok>.md`.
- Pisz po polsku.
```

---

## Wariant „surowy" (jeśli wolisz sam wygenerować dane i wrzucić do Coworka)

Gdyby projekt nie miał agenta z dostępem do gita, odpal lokalnie te komendy
i wrzuć output do Coworka razem z promptem powyżej:

```bash
# Podmień zakres dat. Lista commitów per dzień:
git log --since="2026-05-01" --until="2026-06-01" --reverse \
  --pretty=format:"%ad | %h | %s" --date=format:"%Y-%m-%d %H:%M"

# Zmienione pliki + linie (do opisu co robiłem):
git log --since="2026-05-01" --until="2026-06-01" --numstat \
  --pretty=format:"%n=== %ad | %s" --date=format:"%Y-%m-%d %H:%M"

# (opcjonalnie) tylko moje commity — dodaj do powyższych:
#   --author="twoj@email"
```
