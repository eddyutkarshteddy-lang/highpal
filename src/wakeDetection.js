// Wake detection utility module
// Provides pure functions to tokenize transcripts, merge bigrams, and detect wake phrases.
// This allows easier unit testing and optional backend reuse.

export const BASE_WAKE_WORDS = [
  // Wake word variations
  'pal', 'paul', 'pel', 'pale', 'pail', 'pow', 'pol',
  'listen', 'listenpal', 'heypal'
];

// Precompiled regex for early filtering while AI is speaking
// Matches any wake word pattern
export const POTENTIAL_WAKE_REGEX = /\b(pal|paul|pel|pale|pail|pow|pol|listen|hey pal|listen pal)\b/i;

export function normalizeTranscript(raw) {
  return raw.toLowerCase().replace(/[^a-z\s]/g,' ').replace(/\s+/g,' ').trim();
}

export function tokenize(normalized) {
  if(!normalized) return [];
  return normalized.split(' ').filter(Boolean);
}

export function mergeBigrams(tokens) {
  const result = [...tokens];
  // Merge "hey pal" into "heypal"
  for(let i=0;i<tokens.length-1;i++){
    if(tokens[i]==='hey' && tokens[i+1]==='pal'){
      if(!result.includes('heypal')) result.push('heypal');
    }
    // Merge "listen pal" into "listenpal"
    if(tokens[i]==='listen' && tokens[i+1]==='pal'){
      if(!result.includes('listenpal')) result.push('listenpal');
    }
  }
  return result;
}

// Lightweight Levenshtein for short tokens
export function levDist(a,b){
  const m=a.length,n=b.length; if(m===0) return n; if(n===0) return m;
  const dp=Array.from({length:m+1},()=>Array(n+1).fill(0));
  for(let i=0;i<=m;i++) dp[i][0]=i; for(let j=0;j<=n;j++) dp[0][j]=j;
  for(let i=1;i<=m;i++){
    for(let j=1;j<=n;j++){
      const cost=a[i-1]===b[j-1]?0:1;
      dp[i][j]=Math.min(dp[i-1][j]+1, dp[i][j-1]+1, dp[i-1][j-1]+cost);
    }
  }
  return dp[m][n];
}

// In strict bigram-only mode we don't need fuzzy matching; keep function for API compatibility.
// Simple fuzzy helper for short tokens
function similar(a, b, max=1){
  return levDist(a,b) <= max;
}

// Fuzzy detection for wake words
export function fuzzyMatchTokens(tokens){
  if (!tokens || tokens.length === 0) return null;
  
  // Check for exact wake words
  for (const wake of BASE_WAKE_WORDS) {
    if (tokens.includes(wake)) {
      return { match: wake, kind: 'exact' };
    }
  }
  
  // Check for fuzzy matches with 1-character tolerance
  for (let i = 0; i < tokens.length; i++) {
    const t = tokens[i];
    for (const wake of ['pal', 'paul', 'pel', 'pale', 'pail', 'pow', 'pol']) {
      if (similar(t, wake, 1)) {
        return { match: wake, kind: 'fuzzy' };
      }
    }
  }
  
  // Check for bigram patterns (hey pal, listen pal)
  for (let i = 0; i < tokens.length - 1; i++) {
    const t1 = tokens[i];
    const t2 = tokens[i + 1];
    
    if ((t1 === 'hey' || similar(t1, 'hey', 1)) && 
        (t2 === 'pal' || similar(t2, 'pal', 1))) {
      return { match: 'heypal', kind: 'bigram' };
    }
    
    if ((t1 === 'listen' || similar(t1, 'listen', 1)) && 
        (t2 === 'pal' || similar(t2, 'pal', 1))) {
      return { match: 'listenpal', kind: 'bigram' };
    }
  }
  
  return null;
}

export function simpleContains(normalized, base=BASE_WAKE_WORDS){
  const padded = ` ${normalized} `;
  return base.some(w => {
    // Check for exact word boundaries
    if (padded.includes(` ${w} `)) return true;
    // Check for bigram patterns
    if (w === 'heypal' && padded.includes(' hey pal ')) return true;
    if (w === 'listenpal' && padded.includes(' listen pal ')) return true;
    return false;
  });
}

export function detectWake(rawTranscript, { skipFuzzy=false } = {}) {
  const normalized = normalizeTranscript(rawTranscript||'');
  const tokens = mergeBigrams(tokenize(normalized));
  
  // Check for any wake word in tokens
  let hasWakeWord = false;
  let detectedWords = [];
  
  for (const wake of BASE_WAKE_WORDS) {
    if (tokens.includes(wake)) {
      hasWakeWord = true;
      detectedWords.push(wake);
    }
  }
  
  let matched = null;
  if (!hasWakeWord && !skipFuzzy) {
    const fm = fuzzyMatchTokens(tokens);
    if (fm) {
      hasWakeWord = true;
      matched = fm;
      detectedWords.push(fm.match);
    }
  }
  
  return {
    normalized,
    tokens,
    matched,
    simpleFound: hasWakeWord,
    hasWakeWord: hasWakeWord,
    detectedWakeWords: detectedWords
  };
}

// Early filter: returns true if a probable wake fragment appears (used when AI speaking)
export function passesEarlyFilter(raw){
  return POTENTIAL_WAKE_REGEX.test(raw);
}

// Self-trigger suppression helper
export function suppressIfAIMatch(tokens, aiText, wakeWords=BASE_WAKE_WORDS, elapsedMs, overlapGraceMs=600){
  if(!aiText) return false; // don't suppress
  const aiTokens = new Set(aiText.split(/\s+/));
  const nonOverlap = tokens.find(t => !aiTokens.has(t));
  const wakePresent = tokens.some(t => wakeWords.includes(t));
  if(wakePresent && !nonOverlap && elapsedMs > overlapGraceMs){
    return true; // suppress
  }
  return false;
}

export function analyzeWake(raw, options){
  const detection = detectWake(raw, options);
  return detection;
}

export default {
  BASE_WAKE_WORDS,
  POTENTIAL_WAKE_REGEX,
  normalizeTranscript,
  tokenize,
  mergeBigrams,
  levDist,
  fuzzyMatchTokens,
  simpleContains,
  detectWake,
  passesEarlyFilter,
  suppressIfAIMatch,
  analyzeWake
};