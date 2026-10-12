# Manual acceptance checklist

Run against your local MariaDB installation after following README.md from a fresh
clone. Use accounts you register yourself. No administrator account is required.
Record date, environment, actual result and any defect; do not mark unrun tests passed.

| Check | Steps | Expected result | Your result |
| --- | --- | --- | --- |
| Home desktop | Open home at a desktop width | Publisher introduction and clearly spaced navigation; no permanently visible skip link | Pending |
| Home mobile | Resize to 390px wide | Links wrap without overlaps or horizontal page scrolling | Pending |
| Keyboard | Press Tab from the address bar, focus skip link, press Enter | Skip link appears on focus and moves focus to main content | Pending |
| Registration | Register editor, journalist and reader in separate sessions | Chosen roles work; no Admin access granted | Pending |
| Publisher | Editor creates a company and edits its description | Creator is an editor member; updates persist | Pending |
| Employees | Add the journalist and a second editor by username | They appear under correct headings | Pending |
| Invalid employee | Enter missing username or reader username | Clear validation message; membership unchanged | Pending |
| Company isolation | Unassigned editor tries the company's edit and employee URLs | Access denied; data unchanged | Pending |
| Journalism | Added journalist writes an article for company | Draft saved; company selectable | Pending |
| Reader privacy | Reader visits draft URL | Draft not exposed | Pending |
| Approval | Company editor opens draft and approves | Published; subscriber email appears in console; API logged status true | Pending |
| Subscriptions | Reader follows company and author, then checks subscribed feed | Approved story appears once | Pending |
| Reapproval | Journalist edits published story, then editor approves again | Edit removes approval; current revision published after approval | Pending |
| Newsletter | Editor or journalist curates approved articles and sends | Reader can view; console displays subscriber email | Pending |
| Removal | Editor removes journalist, journalist tries editing company draft | Access denied; account and existing content retained | Pending |
| Last editor | Try removing the only active editor | Helpful error; company retains an editor | Pending |
| Delete | Author/editor opens delete confirmation then submits | Correct story removed; other content preserved | Pending |
| Logout/login | Log out, log back in | Session changes correctly; role navigation returns | Pending |

Console emails validate local message generation, not delivery to an external inbox.
If using SMTP, separately confirm a message arrives in the intended subscriber inbox.
