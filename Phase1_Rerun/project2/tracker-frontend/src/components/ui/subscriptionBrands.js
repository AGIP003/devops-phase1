import {
  si1password,
  siAnthropic,
  siApple,
  siApplemusic,
  siAppletv,
  siAudible,
  siCloudflare,
  siCoursera,
  siCrunchyroll,
  siDeezer,
  siDigitalocean,
  siDiscord,
  siDropbox,
  siFigma,
  siFirebase,
  siGithub,
  siGoogle,
  siGooglecloud,
  siGoogledrive,
  siGooglegemini,
  siGooglephotos,
  siGrammarly,
  siHostinger,
  siIcloud,
  siMax,
  siNetflix,
  siNetlify,
  siNordvpn,
  siNotion,
  siParamountplus,
  siPatreon,
  siPlaystation,
  siRailway,
  siRender,
  siSoundcloud,
  siSpotify,
  siSnapchat,
  siSupabase,
  siTidal,
  siUdemy,
  siVercel,
  siWordpress,
  siX,
  siYoutube,
  siZoom,
} from "simple-icons";

// OpenAI was removed from newer Simple Icons releases. Keep the last
// maintained vector locally so ChatGPT still has a real mark without making a
// third-party network request while rendering the page.
const openAiIcon = {
  hex: "000000",
  path: "M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z",
  title: "OpenAI",
};


function iconBrand(key, aliases, icon) {
  return {
    aliases,
    backgroundColor: "#ffffff",
    color: `#${icon.hex}`,
    icon,
    key,
    title: icon.title,
  };
}

function badgeBrand(
  key,
  aliases,
  label,
  backgroundColor,
  color = "#ffffff",
) {
  return { aliases, backgroundColor, color, key, label, title: label };
}

// Keep specific services before their parent brands: "Apple Music" should not
// be swallowed by the more general "Apple" alias, for example.
const subscriptionBrands = [
  iconBrand("apple-music", ["apple music"], siApplemusic),
  iconBrand("apple-tv", ["apple tv", "apple tv plus"], siAppletv),
  iconBrand("icloud", ["icloud plus", "icloud+", "icloud storage", "icloud"], siIcloud),
  iconBrand("google-cloud", ["google cloud", "gcp"], siGooglecloud),
  iconBrand("google-drive", ["google drive"], siGoogledrive),
  iconBrand("google-photos", ["google photos storage", "google photos"], siGooglephotos),
  iconBrand("google-gemini", ["google gemini", "gemini advanced", "gemini"], siGooglegemini),
  iconBrand("youtube", ["youtube premium", "youtube music", "youtube"], siYoutube),
  iconBrand("digitalocean", ["digital ocean", "digitalocean"], siDigitalocean),
  iconBrand("playstation", ["playstation plus", "play station", "playstation"], siPlaystation),
  iconBrand("paramount-plus", ["paramount plus", "paramount+", "paramount"], siParamountplus),
  iconBrand("one-password", ["1password", "one password"], si1password),
  iconBrand("netflix", ["netflix"], siNetflix),
  iconBrand("spotify", ["spotify"], siSpotify),
  iconBrand("figma", ["figma"], siFigma),
  iconBrand("apple", ["icloud", "apple one", "apple"], siApple),
  iconBrand("github", ["github copilot", "github"], siGithub),
  iconBrand("vercel", ["vercel"], siVercel),
  iconBrand("railway", ["railway app", "railway"], siRailway),
  iconBrand("cloudflare", ["cloudflare"], siCloudflare),
  iconBrand("notion", ["notion"], siNotion),
  iconBrand("dropbox", ["dropbox"], siDropbox),
  iconBrand("zoom", ["zoom"], siZoom),
  iconBrand("grammarly", ["grammarly"], siGrammarly),
  iconBrand("claude", ["anthropic", "claude"], siAnthropic),
  iconBrand("crunchyroll", ["crunchyroll"], siCrunchyroll),
  iconBrand("audible", ["audible"], siAudible),
  iconBrand("tidal", ["tidal"], siTidal),
  iconBrand("deezer", ["deezer"], siDeezer),
  iconBrand("soundcloud", ["sound cloud", "soundcloud"], siSoundcloud),
  iconBrand("max", ["hbo max", "max"], siMax),
  iconBrand("nordvpn", ["nord vpn", "nordvpn"], siNordvpn),
  iconBrand("discord", ["discord nitro", "discord"], siDiscord),
  iconBrand("snapchat", ["snapchat plus", "snapchat+", "snapchat premium", "snapchat"], siSnapchat),
  iconBrand("patreon", ["patreon"], siPatreon),
  iconBrand("coursera", ["coursera"], siCoursera),
  iconBrand("udemy", ["udemy"], siUdemy),
  iconBrand("netlify", ["netlify"], siNetlify),
  iconBrand("render", ["render.com", "render"], siRender),
  iconBrand("supabase", ["supabase"], siSupabase),
  iconBrand("firebase", ["firebase"], siFirebase),
  iconBrand("hostinger", ["hostinger"], siHostinger),
  iconBrand("wordpress", ["wordpress"], siWordpress),
  iconBrand("x", ["x premium", "twitter premium", "twitter blue"], siX),
  iconBrand("google", ["google one", "google"], siGoogle),
  iconBrand("chatgpt", ["chat gpt", "chatgpt", "open ai", "openai"], openAiIcon),

  badgeBrand("viu-to", ["viu.to", "viu to"], "Viu", "#111827"),
  badgeBrand("viu", ["viu premium", "viu"], "Viu", "#f6c700", "#111111"),
  badgeBrand("kenya-power", ["kenya power", "kplc", "my power"], "KP", "#f4c300", "#1d2530"),
  badgeBrand("safaricom", ["safaricom home fibre", "safaricom home", "safaricom"], "S", "#00a651"),
  badgeBrand("zuku", ["wananchi", "zuku"], "Z", "#6f2c91"),
  badgeBrand("dstv", ["dstv", "d stv"], "D", "#0878c9"),
  badgeBrand("gotv", ["gotv", "go tv"], "GO", "#65a30d"),
  badgeBrand("startimes", ["star times", "startimes"], "ST", "#f97316"),
  badgeBrand("showmax", ["showmax"], "SM", "#e6007e"),
  badgeBrand("poa", ["poa internet", "poa"], "poa", "#075985"),
  badgeBrand("faiba", ["jtl faiba", "faiba"], "F", "#e6007e"),
  badgeBrand("airtel", ["airtel"], "A", "#ed1c24"),
  badgeBrand("starlink", ["starlink"], "SL", "#111827"),
  badgeBrand("amazon-prime", ["amazon prime video", "prime video", "amazon prime"], "P", "#00a8e1"),
  badgeBrand("disney-plus", ["disney plus", "disney+"], "D+", "#113ccf"),
  badgeBrand("canva", ["canva"], "C", "#7d2ae8"),
  badgeBrand("adobe", ["adobe creative cloud", "adobe"], "A", "#eb1000"),
  badgeBrand("microsoft-365", ["microsoft 365", "office 365"], "M", "#2563eb"),
  badgeBrand("aws", ["amazon web services", "aws"], "AWS", "#232f3e"),
  badgeBrand("azure", ["microsoft azure", "azure"], "AZ", "#0078d4"),
  badgeBrand("slack", ["slack"], "S", "#611f69"),
  badgeBrand("heroku", ["heroku"], "H", "#430098"),
  badgeBrand("glovo", ["glovo prime", "glovo"], "G", "#ffc244", "#1f2937"),
  badgeBrand("uber-one", ["uber one", "uber"], "U", "#111111"),
  badgeBrand("nairobi-water", ["nairobi water", "ncwsc"], "NW", "#0369a1"),
  badgeBrand("sha", ["social health authority", "shif", "sha"], "SHA", "#047857"),
];

export function normalizeSubscriptionBrand(value) {
  return String(value || "")
    .normalize("NFKD")
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/g, "");
}

export function resolveSubscriptionBrand(subscription) {
  const searchable = normalizeSubscriptionBrand(
    `${subscription?.provider || ""} ${subscription?.name || ""}`,
  );

  if (!searchable) return null;
  return subscriptionBrands.find((brand) => (
    brand.aliases.some((alias) => (
      searchable.includes(normalizeSubscriptionBrand(alias))
    ))
  )) || null;
}

export default subscriptionBrands;
