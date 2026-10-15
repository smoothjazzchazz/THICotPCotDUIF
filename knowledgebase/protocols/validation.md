# Documentation validation

Date: 12 October 2026. These checks concern this reference set, not firmware, trained receivers, RTL, or physical interfaces.

## Reproduce local checks

From the repository root:

```sh
python3 knowledgebase/protocols/verify.py
git diff --check
```

The checker uses only Python's standard library and writes no files. It validates:

- UART example bit order, parity arithmetic, frame lengths, and chosen-baud durations.
- I2C address bytes and MSB-first representations in the worked combined transfer.
- USB token CRC5, SETUP-payload CRC16, empty-payload CRC16, complemented PIDs, and the NRZI fragment. It compares left-shifting specification and reflected software conventions and checks the specified receiver residues.
- Ethernet example padding/length, FCS via reflected calculation, standard-library CRC32, and independent polynomial division; it compares their emitted bits. Corrupting a protected bit or incorrectly including preamble/SFD changes the FCS. It also checks simulation tick arithmetic.
- Worked numeric values still appear in the guides, local documentation links resolve, the retained source PDF matches its manifest checksum/size, and all four placeholders still report missing implementation/hardware evidence.

Recorded result: example checks passed; 16 source records and the one retained PDF checksum passed; local links and all four evidence statuses passed. The final documentation whitespace/diff checks also passed. These results do not constitute protocol qualification.

## Source and scenario review

| Scenario | Review performed | Boundary |
| --- | --- | --- |
| UART bad parity, low stop, break, adjacent frames | Compared with U1 §2.4, §3.6, §3.8 and U2; inspected rendered framing figure | Does not measure any receiver's baud tolerance or break recovery |
| I2C repeated START, receiver ACK, read-final NACK, stretching | Walked through ownership and transitions against I1 §3.1.4–3.1.9; inspected rendered Table 11 and footnotes | Does not qualify analog timing, arbitration, or the current peer's recovery |
| USB stuffing across fields/CRC, EOP, retries, control exchange | Checked B1 §7.1.7–7.1.10, §8.3.5, §8.5–8.6, §9.4.6; inspected rendered CRC page; applied relevant B2/B3 corrections | The checker is arithmetic only; no USB device/peer implementation or interoperability test was added |
| Ethernet padding, FCS order, SFD/frame boundary, gap and PHY idle | Checked E1 §3.2–3.4, Table 4-2, §7.3.1.1 and clause 14; inspected rendered FCS page and all E2 corrections | A computed frame is not the required TX-table/streaming simulation or a working link |

The source register distinguishes full relevant-section checks from ECN scope screening. USB electrical/connector/host/hub/class qualification is not complete. Ethernet uses the disclosed older mirror copy; newest-edition verification and publisher byte authentication remain unresolved. Neither limitation is hidden behind a generic “compliant” claim.

## Preservation

Only agent guidance and knowledgebase documentation/supporting reference checks were changed. The original studies, frozen results, reference specifications, runtime models, RTL, clock claims, and phase gates remain untouched. The untracked UART follow-up present before this task remains outside this audit.

The retained IEEE correction sheet is an unchanged original, with its own noncommercial redistribution conditions. The main standards/manuals remain linked rather than copied where permission was not established.
