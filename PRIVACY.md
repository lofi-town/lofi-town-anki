# Privacy

Last updated: August 19, 2026

## Add-on data

Lofi Town for Anki does not read, upload, edit, or reschedule decks, cards,
answers, review history, or other Anki collection data.

The add-on stores these items locally:

- Panel visibility, position, size, zoom, and appearance settings.
- An isolated browser profile, including Lofi Town cookies, local storage, and
  cache files, inside the add-on's `user_files/` directory.

The review answer count and focus timer are kept in memory for the current
review session. They reset when the reviewer or Anki profile closes.

## Lofi Town service

The panel loads `https://app.lofi.town`. Network requests, account information,
and service activity are handled by Lofi Town under the
[Lofi Town privacy policy](https://www.lofi.town/privacy-policy).

The add-on does not send Anki collection data to the Lofi Town service. Its
isolated browser profile is separate from the user's normal web browser.

## Sign-in

Google and Discord sign-in open in the system browser. The response returns to
a random, single-use address on `127.0.0.1` that expires after five minutes.
The add-on does not log or persist the authorization code.

## Removing data

Delete the add-on through **Tools > Add-ons** to remove it from Anki. If a
manually managed copy remains, close Anki and remove its `user_files/web-profile`
and `user_files/web-cache` directories to clear the local Lofi Town session and
cache.

Removing local add-on data does not delete a Lofi Town account. See the
[Lofi Town privacy policy](https://www.lofi.town/privacy-policy) for account and
data requests.

Privacy questions can be sent to `contact@lofi.town`. Report security issues
privately according to [SECURITY.md](SECURITY.md).
