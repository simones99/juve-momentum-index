export type Locale = "it" | "en";

export const LOCALES: Locale[] = ["it", "en"];
export const DEFAULT_LOCALE: Locale = "it";
export const LOCALE_COOKIE = "locale";

export interface Dictionary {
  htmlLang: string;
  nav: {
    overview: string;
    momentumDetails: string;
    matches: string;
    matchBrief: string;
    trasferte: string;
  };
  sidebar: {
    nextMatch: string;
    noUpcoming: string;
  };
  footer: string;
  common: {
    home: string;
    away: string;
    allSeasons: string;
    allCompetitions: string;
    filter: string;
    search: string;
    searching: string;
    noDataForSelection: string;
  };
  overview: {
    subtitle: string;
    kpi: {
      maxMomentum: string;
      minMomentum: string;
      longestWinStreak: string;
      currentStreak: string;
    };
    momentumOverTime: string;
  };
  recentMatches: {
    title: string;
    emptyState: string;
  };
  upcomingMatches: {
    title: string;
    emptyState: string;
    venueTbd: string;
  };
  momentum: {
    subtitle: string;
    homeAwaySelect: string;
    matchDetailTitle: string;
    eloVsMomentum: string;
    emptyState: string;
    table: {
      date: string;
      opponent: string;
      homeAway: string;
      result: string;
      eloBeforeAfter: string;
      momentum: string;
    };
  };
  matches: {
    subtitle: (total: number) => string;
    table: {
      date: string;
      competition: string;
      home: string;
      away: string;
      result: string;
      outcome: string;
    };
    emptyState: string;
    pagination: {
      previous: string;
      next: string;
      pageOf: (page: number, total: number) => string;
    };
    filters: {
      allResults: string;
      win: string;
      draw: string;
      loss: string;
      opponentPlaceholder: string;
    };
  };
  matchDetail: {
    briefNotAvailable: string;
    matchNotPlayedYet: string;
  };
  brief: {
    title: string;
    subtitle: string;
    noBriefFound: string;
    preTitle: string;
    postTitle: string;
    aiEnhanced: string;
    template: string;
    resultLabel: string;
    momentumIndexLabel: string;
    eloLabel: string;
    trendEloLabel: string;
    trend: { up: string; down: string; flat: string };
    probTitlePre: string;
    probTitlePost: string;
    drawLabel: string;
    basedOnHistory: string;
    aiUnavailableNote: string;
  };
  trasferte: {
    subtitle: string;
    searchPlaceholder: string;
    searchButton: string;
    searchingButton: string;
    errorGeneric: string;
    promptEmptyState: string;
    departureLabel: (name: string) => string;
    tripsCountLabel: (n: number) => string;
    noTripsScheduled: string;
    noTripDataAvailable: string;
    difficultyTitle: string;
    table: {
      date: string;
      opponent: string;
      stadium: string;
      distance: string;
      travelDuration: string;
      difficulty: string;
      dayTrip: string;
    };
    yes: string;
    no: string;
    estimateSuffix: string;
    disclaimer: string;
    feasible: string;
    notFeasible: string;
  };
  resultBadge: { W: string; D: string; L: string };
  live: {
    badge: string;
    halftime: string;
    probTitle: string;
    approxNote: string;
  };
}

export const dictionaries: Record<Locale, Dictionary> = {
  it: {
    htmlLang: "it",
    nav: {
      overview: "Overview",
      momentumDetails: "Momentum Details",
      matches: "Matches",
      matchBrief: "Match Brief",
      trasferte: "Trasferte",
    },
    sidebar: {
      nextMatch: "Prossima partita",
      noUpcoming: "Nessuna partita in programma",
    },
    footer:
      "Dati indicativi da football-data.org (fallback Wikipedia). Progetto personale, non affiliato alla Juventus FC.",
    common: {
      home: "Casa",
      away: "Trasferta",
      allSeasons: "Tutte le stagioni",
      allCompetitions: "Tutte le competizioni",
      filter: "Filtra",
      search: "Cerca",
      searching: "Cerco…",
      noDataForSelection: "Nessun dato disponibile per questa selezione.",
    },
    overview: {
      subtitle: "Andamento del Momentum Index della Juventus nel tempo.",
      kpi: {
        maxMomentum: "Momentum massimo",
        minMomentum: "Momentum minimo",
        longestWinStreak: "Serie vittorie più lunga",
        currentStreak: "Striscia attuale",
      },
      momentumOverTime: "Momentum Index nel tempo",
    },
    recentMatches: {
      title: "Ultime partite",
      emptyState: "Nessuna partita giocata nel dataset al momento.",
    },
    upcomingMatches: {
      title: "Prossime partite",
      emptyState: "Nessuna partita in programma nel dataset al momento.",
      venueTbd: "Sede da confermare",
    },
    momentum: {
      subtitle: "Elo, forma recente e Momentum Index partita per partita.",
      homeAwaySelect: "Casa/Trasferta",
      matchDetailTitle: "Dettaglio partite",
      eloVsMomentum: "Elo vs Momentum Index",
      emptyState: "Nessun dato per questa selezione.",
      table: {
        date: "Data",
        opponent: "Avversario",
        homeAway: "C/T",
        result: "Esito",
        eloBeforeAfter: "Elo prima → dopo",
        momentum: "Momentum",
      },
    },
    matches: {
      subtitle: (total) => `Tutte le partite della Juventus nel dataset (${total} totali).`,
      table: {
        date: "Data",
        competition: "Competizione",
        home: "Casa",
        away: "Trasferta",
        result: "Risultato",
        outcome: "Esito",
      },
      emptyState: "Nessuna partita trovata con questi filtri.",
      pagination: {
        previous: "← Precedente",
        next: "Successiva →",
        pageOf: (page, total) => `Pagina ${page} di ${total}`,
      },
      filters: {
        allResults: "Tutti i risultati",
        win: "Vittoria",
        draw: "Pareggio",
        loss: "Sconfitta",
        opponentPlaceholder: "Avversario",
      },
    },
    matchDetail: {
      briefNotAvailable: "Brief non ancora disponibile per questa partita.",
      matchNotPlayedYet: "Partita non ancora giocata: consulta il Brief pre-partita nella sezione dedicata.",
    },
    brief: {
      title: "Match Brief",
      subtitle: "Anteprima basata sulle ultime partite della Juventus.",
      noBriefFound: "Nessuna partita programmata trovata nel dataset al momento.",
      preTitle: "Brief pre-partita",
      postTitle: "Brief post-partita",
      aiEnhanced: "AI-enhanced",
      template: "Template",
      resultLabel: "Risultato",
      momentumIndexLabel: "Momentum Index",
      eloLabel: "Elo",
      trendEloLabel: "Trend Elo",
      trend: { up: "in crescita", down: "in calo", flat: "stabile" },
      probTitlePre: "Probabilità di risultato",
      probTitlePost: "Probabilità prima della partita",
      drawLabel: "Pareggio",
      basedOnHistory: "Basato sullo storico delle partite — indovina il risultato circa nel 56% dei casi.",
      aiUnavailableNote: "Nota: generazione AI non disponibile in questo momento, mostrato il testo template.",
    },
    trasferte: {
      subtitle: "Trova le prossime trasferte della Juve più facili da raggiungere dalla tua città.",
      searchPlaceholder: "Città di partenza (es. Ancona)",
      searchButton: "Cerca",
      searchingButton: "Cerco…",
      errorGeneric: "Errore imprevisto durante la ricerca.",
      promptEmptyState: "Inserisci una città per vedere le prossime trasferte della Juve ordinate per difficoltà.",
      departureLabel: (name) => `Partenza: ${name}`,
      tripsCountLabel: (n) => `${n} trasferte in programma`,
      noTripsScheduled:
        "Nessuna trasferta programmata nel dataset al momento (serve un'ingestion con calendario reale — vedi README).",
      noTripDataAvailable: "Nessuna trasferta con dati di viaggio disponibili.",
      difficultyTitle: "Difficoltà per trasferta",
      table: {
        date: "Data",
        opponent: "Avversario",
        stadium: "Stadio",
        distance: "Distanza",
        travelDuration: "Durata viaggio",
        difficulty: "Difficoltà",
        dayTrip: "Giornata?",
      },
      yes: "Sì",
      no: "No",
      estimateSuffix: " (stima)",
      disclaimer:
        'Stima indicativa basata su distanza/tempo di guida in auto e orario della partita — non tiene conto di orari treni, traffico reale o eventi. "Giornata" = presumibilmente fattibile andata e ritorno in giornata partendo non prima delle 4:00 e rientrando entro le 2:00 di notte.',
      feasible: "andata/ritorno in giornata",
      notFeasible: "richiede pernottamento",
    },
    resultBadge: { W: "V", D: "N", L: "P" },
    live: {
      badge: "LIVE",
      halftime: "Intervallo",
      probTitle: "Probabilità live (stima)",
      approxNote: "Stima live approssimata, aggiornata col punteggio — non è un modello calibrato sul minuto di gioco.",
    },
  },
  en: {
    htmlLang: "en",
    nav: {
      overview: "Overview",
      momentumDetails: "Momentum Details",
      matches: "Matches",
      matchBrief: "Match Brief",
      trasferte: "Away Trips",
    },
    sidebar: {
      nextMatch: "Next match",
      noUpcoming: "No match scheduled",
    },
    footer:
      "Indicative data from football-data.org (Wikipedia fallback). Personal project, not affiliated with Juventus FC.",
    common: {
      home: "Home",
      away: "Away",
      allSeasons: "All seasons",
      allCompetitions: "All competitions",
      filter: "Filter",
      search: "Search",
      searching: "Searching…",
      noDataForSelection: "No data available for this selection.",
    },
    overview: {
      subtitle: "Juventus' Momentum Index trend over time.",
      kpi: {
        maxMomentum: "Highest momentum",
        minMomentum: "Lowest momentum",
        longestWinStreak: "Longest win streak",
        currentStreak: "Current streak",
      },
      momentumOverTime: "Momentum Index over time",
    },
    recentMatches: {
      title: "Recent matches",
      emptyState: "No played matches in the dataset yet.",
    },
    upcomingMatches: {
      title: "Upcoming matches",
      emptyState: "No matches scheduled in the dataset yet.",
      venueTbd: "Venue to be confirmed",
    },
    momentum: {
      subtitle: "Elo, recent form, and Momentum Index match by match.",
      homeAwaySelect: "Home/Away",
      matchDetailTitle: "Match details",
      eloVsMomentum: "Elo vs Momentum Index",
      emptyState: "No data for this selection.",
      table: {
        date: "Date",
        opponent: "Opponent",
        homeAway: "H/A",
        result: "Outcome",
        eloBeforeAfter: "Elo before → after",
        momentum: "Momentum",
      },
    },
    matches: {
      subtitle: (total) => `All Juventus matches in the dataset (${total} total).`,
      table: {
        date: "Date",
        competition: "Competition",
        home: "Home",
        away: "Away",
        result: "Score",
        outcome: "Outcome",
      },
      emptyState: "No matches found with these filters.",
      pagination: {
        previous: "← Previous",
        next: "Next →",
        pageOf: (page, total) => `Page ${page} of ${total}`,
      },
      filters: {
        allResults: "All outcomes",
        win: "Win",
        draw: "Draw",
        loss: "Loss",
        opponentPlaceholder: "Opponent",
      },
    },
    matchDetail: {
      briefNotAvailable: "Brief not available yet for this match.",
      matchNotPlayedYet: "Match not played yet: check the pre-match Brief in the dedicated section.",
    },
    brief: {
      title: "Match Brief",
      subtitle: "Preview based on Juventus' latest matches.",
      noBriefFound: "No scheduled match found in the dataset yet.",
      preTitle: "Pre-match brief",
      postTitle: "Post-match brief",
      aiEnhanced: "AI-enhanced",
      template: "Template",
      resultLabel: "Result",
      momentumIndexLabel: "Momentum Index",
      eloLabel: "Elo",
      trendEloLabel: "Elo trend",
      trend: { up: "rising", down: "falling", flat: "stable" },
      probTitlePre: "Outcome probability",
      probTitlePost: "Pre-match probability",
      drawLabel: "Draw",
      basedOnHistory: "Based on match history — guesses the outcome correctly about 56% of the time.",
      aiUnavailableNote: "Note: AI generation is unavailable right now, showing the template text.",
    },
    trasferte: {
      subtitle: "Find Juve's upcoming away trips ranked by how easy they are to reach from your city.",
      searchPlaceholder: "Departure city (e.g. Turin)",
      searchButton: "Search",
      searchingButton: "Searching…",
      errorGeneric: "Unexpected error while searching.",
      promptEmptyState: "Enter a city to see Juve's upcoming away trips ranked by difficulty.",
      departureLabel: (name) => `Departing from: ${name}`,
      tripsCountLabel: (n) => `${n} away trips scheduled`,
      noTripsScheduled:
        "No away trips scheduled in the dataset yet (requires ingestion with a real fixture calendar — see README).",
      noTripDataAvailable: "No away trips with travel data available.",
      difficultyTitle: "Difficulty by trip",
      table: {
        date: "Date",
        opponent: "Opponent",
        stadium: "Stadium",
        distance: "Distance",
        travelDuration: "Travel time",
        difficulty: "Difficulty",
        dayTrip: "Day trip?",
      },
      yes: "Yes",
      no: "No",
      estimateSuffix: " (estimated)",
      disclaimer:
        'Indicative estimate based on driving distance/time and kickoff time — does not account for train schedules, real traffic, or events. "Day trip" = presumably feasible to go and return the same day, leaving no earlier than 4:00 and getting back by 2:00 at night.',
      feasible: "day trip feasible",
      notFeasible: "requires an overnight stay",
    },
    resultBadge: { W: "W", D: "D", L: "L" },
    live: {
      badge: "LIVE",
      halftime: "Half-time",
      probTitle: "Live probability (estimate)",
      approxNote: "Approximate live estimate, updated with the score — not a model calibrated on match minute.",
    },
  },
};
