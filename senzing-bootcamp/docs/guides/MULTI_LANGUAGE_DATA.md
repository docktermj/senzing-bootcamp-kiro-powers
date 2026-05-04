# Multi-Language Entity Resolution

Real-world entity resolution rarely deals with a single language. Customer databases span multiple countries, compliance screening crosses jurisdictions, and the same person or organization can appear in records written in English, Chinese, Arabic, Cyrillic, or any number of other scripts. A name like "John Smith" in one system might appear as "约翰·史密斯" in another, and an address in Latin characters in one source might be recorded in its original Arabic or Devanagari script elsewhere. These variations are not errors — they are the natural result of operating across languages and writing systems. Without proper handling, multi-language data leads to missed matches, duplicate entities, and incomplete resolution results. This guide covers how Senzing handles non-Latin characters natively, what encoding requirements your data must meet, how cross-script name matching works, and best practices for preparing multi-language data for entity resolution.

## Non-Latin Character Support

Senzing processes non-Latin characters natively — you do not need to translate or romanize your data before loading it. The engine accepts UTF-8 encoded input in any script and performs its own internal analysis to understand, store, and match names across writing systems. If your source data contains names in Chinese, Arabic, Cyrillic, or any other non-Latin script, load them as-is. Pre-translating names before loading actually removes information that Senzing uses for matching.

### Supported Script Families

Senzing supports name matching across a broad range of cultural groups and writing systems. For personal names, Senzing leverages culturally-aware name comparison that uses spelling patterns and country-of-association information to determine cultural provenance and optimize matching strategies.

The primary cultural groups supported for personal name matching include:

| Cultural Group | Scripts and Languages | Example (Original → Transliteration) |
| --- | --- | --- |
| Southwest Asian | Arabic, Farsi, Afghan, Pakistani | محمد حسن الشمري → Mohammed Hassan Al-Shamri |
| European | Latin (Anglo, French, German, Hispanic, Polish, Portuguese) | François Müller → Francois Mueller |
| Han | Chinese, Korean, Vietnamese | 王小明 → Wang Xiaoming |
| East Slavic | Cyrillic (Russian, Ukrainian, Belarusian) | Александр Петров → Aleksandr Petrov |
| Indian | Devanagari and related scripts | राम कुमार शर्मा → Ram Kumar Sharma |
| Japanese | Hiragana, Katakana | さとう ひろし → Satou Hiroshi |
| Turkish | Latin with Turkish-specific characters | Mustafa Özkan → Mustafa Ozkan |
| Yoruban | Latin with West African diacritics | Adébáyọ̀ Ọlátúndé → Adebayo Olatunde |
| Indonesian | Latin with diacritics | Standard Latin script |

> **Note:** Japanese Kanji is not directly handled by Senzing and is treated as Chinese Hanzi when provided.

For organizational names, Senzing provides same-script matching across Arabic, Cyrillic, Latin (with diacritics), Japanese, Korean, and Chinese scripts. Starting in v4, Senzing also supports native cross-script matching between CJK (Chinese, Japanese, Korean) and English organizational names without requiring reference data.

### How Senzing Stores and Indexes Names

When you load a record containing a name in a non-Latin script, Senzing stores the original name exactly as provided and generates transliterated forms internally for cross-script comparison. The engine uses ICU (International Components for Unicode) to normalize data for cross-script comparisons — for example, matching the same name written in Latin and Arabic scripts. In certain areas, Senzing goes beyond ICU with additional culturally-aware matching logic.

This means a single name in your data can participate in matches against records in multiple scripts. A record with `NAME_FULL` set to `"محمد حسن"` (Arabic) can match against a record with `NAME_FULL` set to `"Mohammed Hassan"` (Latin) because Senzing maintains both the original script and its transliterated representations in the index.

When your source data already contains both native-script and romanized versions of a name, best practice is to include both in the same record using different name usage types. This gives the engine multiple representations to work with and improves matching accuracy.

### Example: Loading a Record with Non-Latin Characters

The following Senzing Entity Specification (SGES) record contains a Chinese name and address. No pre-translation is needed — load the record exactly as shown:

```json
{
  "DATA_SOURCE": "CUSTOMERS_APAC",
  "RECORD_ID": "CN-10042",
  "NAME_FULL": "李明",
  "ADDR_FULL": "北京市朝阳区建国路88号",
  "PHONE_NUMBER": "+86-10-5555-0123"
}
```

Senzing stores `"李明"` in its original Chinese script and generates the transliterated form (e.g., "Li Ming") internally. This record can match against a Latin-script record containing `"Li Ming"` or `"Lee Ming"` as the name, without any manual mapping between the two forms.

When both a native-script name and a romanized name are available in your source data, include both in the record:

```json
{
  "DATA_SOURCE": "CUSTOMERS_APAC",
  "RECORD_ID": "CN-10043",
  "PRIMARY_NAME_FULL": "王小明",
  "NATIVE_NAME_FULL": "王小明",
  "NAME_FULL": "Wang Xiaoming",
  "ADDR_FULL": "上海市浦东新区陆家嘴环路1000号",
  "PHONE_NUMBER": "+86-21-5555-0456"
}
```

This gives Senzing both representations to work with, improving the chances of matching against records that may only have one form or the other.

## UTF-8 Encoding Requirements

Senzing requires all input data to be UTF-8 encoded. This applies whether you are loading records through the SDK APIs, a bulk loader, or any other ingestion path — the JSON record data passed to Senzing must be valid UTF-8. UTF-8 is the standard encoding for Unicode and can represent every character in every writing system covered in this guide. If your data is not UTF-8, characters will be misinterpreted, names will not match correctly, and records may fail to load entirely.

### Why Encoding Matters for Entity Resolution

Encoding problems are particularly damaging in entity resolution because they corrupt the very data that drives matching. A name stored in Latin-1 encoding might look correct when viewed in a Latin-1-aware editor, but when Senzing reads those bytes as UTF-8, the result is garbled text — a phenomenon called mojibake. A corrupted name cannot match against its correct counterpart, so what should be a single resolved entity becomes two or more unresolved duplicates. Worse, encoding corruption is often silent: the data loads without errors, but matching quality degrades in ways that are difficult to diagnose after the fact.

### Common Encoding Problems

These are the encoding issues most frequently encountered when preparing multi-language data for Senzing:

**Legacy single-byte encodings (Latin-1, Windows-1252).** Data exported from older European systems or Windows applications often uses Latin-1 (ISO 8859-1) or Windows-1252 instead of UTF-8. Characters like `ü`, `ñ`, and `ø` are encoded as single bytes in these formats but require two bytes in UTF-8. Loading Latin-1 data as if it were UTF-8 produces mojibake — for example, `François` becomes `FranÃ§ois` and will not match against a correctly encoded record.

**CJK legacy encodings (Shift-JIS, GB2312, EUC-KR, Big5).** East Asian data from legacy systems frequently uses region-specific encodings: Shift-JIS for Japanese, GB2312 or GBK for Simplified Chinese, Big5 for Traditional Chinese, and EUC-KR for Korean. These multi-byte encodings are incompatible with UTF-8. A Chinese name encoded in GB2312 will produce completely different byte sequences than the same name in UTF-8, resulting in garbled characters and failed matches.

**Byte-order marks (BOM).** Some editors and export tools prepend a UTF-8 byte-order mark (`EF BB BF`) to the beginning of files. While technically valid UTF-8, a BOM at the start of a JSON file can cause parsing failures because the JSON specification does not expect leading bytes before the opening `{` or `[`. If your JSON files have a BOM, strip it before loading.

**Double-encoding (mojibake from re-encoding).** Double-encoding happens when data that is already UTF-8 gets encoded as UTF-8 a second time — typically when a pipeline incorrectly treats UTF-8 bytes as Latin-1 and then converts them to UTF-8. The result is that multi-byte characters balloon into longer sequences of garbled text. For example, the Chinese character `李` (3 bytes in UTF-8) becomes 6 bytes of nonsense after double-encoding. Double-encoded data may load without errors but will never match correctly.

### Senzing Behavior on Invalid UTF-8 Input

Senzing expects valid UTF-8 in all JSON record data. When invalid bytes are encountered during loading, the behavior depends on the ingestion method:

When using a bulk loader such as G2Loader, invalid byte sequences trigger a decode error that halts processing of the affected record. The loader reports the invalid byte value and its position in the file, allowing you to locate and fix the problem. Records before and after the invalid one continue to process normally — a single bad record does not stop the entire load.

When calling the SDK APIs directly (e.g., `add_record`), the JSON record string must be valid UTF-8 before it reaches Senzing. If your application passes a string containing invalid UTF-8 byte sequences, the JSON parser will reject it with a parsing error and the record will not be added. The API returns an error indicating the record could not be processed.

In both cases, Senzing does not silently accept invalid UTF-8 and does not attempt to guess the intended encoding. Data that is not valid UTF-8 must be fixed at the source before loading.

> **Note:** Even when invalid bytes do not cause an outright error — for example, when data is technically valid UTF-8 but was double-encoded — the resulting garbled text will be stored and indexed as-is. Senzing will not be able to match these corrupted values against correctly encoded records. Always verify encoding before loading, not after.

### Encoding Verification and Conversion Checklist

Before loading multi-language data into Senzing, work through these steps to verify and fix encoding issues.

#### 1. Check the file encoding

Use the `file` command to detect the encoding of your data files:

```bash
file -i your_data.json
```

Expected output for a correctly encoded file:

```text
your_data.json: application/json; charset=utf-8
```

If you see `charset=iso-8859-1`, `charset=unknown-8bit`, or any encoding other than `utf-8` or `us-ascii` (which is a subset of UTF-8), the file needs conversion.

For large files, `file` only checks the first few kilobytes by default. On version 5.26+, scan the entire file to catch encoding issues that appear later:

```bash
file_size=$(wc -c < your_data.json)
file -P bytes=$file_size -i your_data.json
```

#### 2. Use chardet for ambiguous files

When `file` reports `unknown-8bit` or you suspect the detection is wrong, use Python's `chardet` library for a more thorough analysis:

```bash
pip install chardet
chardetect your_data.json
```

This scans the file and reports the detected encoding with a confidence score:

```text
your_data.json: GB2312 with confidence 0.99
```

#### 3. Convert to UTF-8 with iconv

Once you know the source encoding, convert to UTF-8 using `iconv`:

```bash
iconv -f ISO-8859-1 -t UTF-8 input.json -o output.json
```

For CJK encodings:

```bash
iconv -f SHIFT-JIS -t UTF-8 japanese_data.json -o japanese_data_utf8.json
iconv -f GB2312 -t UTF-8 chinese_data.json -o chinese_data_utf8.json
iconv -f EUC-KR -t UTF-8 korean_data.json -o korean_data_utf8.json
```

If `iconv` encounters bytes it cannot convert, it stops with an error. Use the `//IGNORE` flag to skip invalid characters rather than halting:

```bash
iconv -f ISO-8859-1 -t UTF-8//IGNORE input.json -o output.json
```

> **Caution:** Using `//IGNORE` silently drops characters that cannot be converted. Review the output to confirm no important data was lost. Fixing the source data is always preferable to ignoring conversion errors.

#### 4. Strip the BOM if present

Check for and remove a UTF-8 BOM:

```bash
# Check for BOM (first 3 bytes will be EF BB BF)
hexdump -C your_data.json | head -1

# Remove BOM using sed
sed -i '1s/^\xEF\xBB\xBF//' your_data.json
```

#### 5. Validate the converted file

After conversion, verify the file is valid UTF-8 and that the content looks correct:

```bash
# Confirm encoding is now UTF-8
file -i output.json

# Spot-check non-Latin characters render correctly
head -20 output.json
```

If non-Latin characters appear as `?`, `�`, or garbled sequences after conversion, the source encoding detection was likely wrong. Go back to step 2 and try a different source encoding.

## Transliteration and Cross-Script Name Matching

One of Senzing's most powerful globalization capabilities is its ability to match names across different writing systems. When the same person appears as "John Smith" in one data source and "约翰·史密斯" in another, or as "Александр Петров" in a Cyrillic record and "Aleksandr Petrov" in a Latin one, Senzing can recognize these as referring to the same entity. This cross-script matching works without requiring you to pre-transliterate your data or maintain manual mapping tables between scripts.

### How Cross-Script Matching Works

Senzing uses ICU (International Components for Unicode) as a foundation for normalizing data across scripts, and extends beyond ICU with culturally-aware matching logic tailored to specific language families. When a record is loaded, Senzing generates internal transliterated representations of names alongside the original script. These transliterated forms are used to compare names that were originally written in different writing systems.

For personal names, Senzing applies culturally-aware name comparison that considers spelling patterns and country-of-association to determine cultural provenance. This means the engine does not rely on a single generic transliteration — it uses knowledge of how names work in specific cultures to produce better phonetic equivalences. For example, the Arabic name "محمد" can be romanized as "Muhammad", "Mohammed", "Mohamed", or "Mohamad" depending on regional conventions. Senzing's matching accounts for these variations rather than requiring an exact transliteration match.

For organizational names, Senzing v4 introduced native cross-script matching between CJK (Chinese, Japanese, Korean) and English without requiring reference data. This is a significant advancement — previously, matching organization names across scripts required bridge records or reference data containing both script versions. For other script combinations, organizational name matching may still benefit from reference data, since organizations handle name translation inconsistently: some transliterate phonetically, some translate semantically, and some rebrand entirely when entering new markets.

Senzing also supports cross-script address matching. Starting in v4, native CJK-to-English address matching works without reference data. For other language combinations, providing both native-script and romanized address versions improves matching accuracy.

### Example 1: Latin and Chinese Name Matching

These two records contain the same person's name in Latin and Chinese scripts. Senzing resolves them to the same entity through its internal transliteration and cross-script comparison:

```json
{
  "DATA_SOURCE": "CUSTOMERS_US",
  "RECORD_ID": "US-20001",
  "NAME_FULL": "Wang Xiaoming",
  "ADDR_FULL": "1000 Lujiazui Ring Road, Pudong, Shanghai",
  "PHONE_NUMBER": "+1-555-0198"
}
```

```json
{
  "DATA_SOURCE": "CUSTOMERS_APAC",
  "RECORD_ID": "CN-20001",
  "NAME_FULL": "王小明",
  "ADDR_FULL": "上海市浦东新区陆家嘴环路1000号",
  "PHONE_NUMBER": "+86-21-5555-0198"
}
```

Senzing generates the transliteration "Wang Xiaoming" from the Chinese characters "王小明" internally and matches it against the Latin-script name in the first record. The shared phone number and address provide additional evidence, but the name match alone is sufficient to link these records when the transliteration aligns.

### Example 2: Latin and Cyrillic Name Matching

These records show the same person's name in Latin and Cyrillic scripts. Senzing's East Slavic cultural group handling recognizes the phonetic equivalence:

```json
{
  "DATA_SOURCE": "PARTNERS_EU",
  "RECORD_ID": "EU-30010",
  "NAME_FULL": "Aleksandr Petrov",
  "ADDR_FULL": "15 Rue de la Paix, Paris, France",
  "DATE_OF_BIRTH": "1985-03-12"
}
```

```json
{
  "DATA_SOURCE": "PARTNERS_RU",
  "RECORD_ID": "RU-30010",
  "NAME_FULL": "Александр Петров",
  "ADDR_FULL": "ул. Тверская 25, Москва, Россия",
  "DATE_OF_BIRTH": "1985-03-12"
}
```

Senzing transliterates "Александр Петров" to its Latin equivalent and matches it against "Aleksandr Petrov". Common transliteration variants like "Alexander Petrov" or "Alexandr Petrov" are also handled through the culturally-aware matching logic for the East Slavic cultural group.

### Example 3: Latin and Arabic Name Matching

These records contain the same person's name in Latin and Arabic scripts. Arabic names present additional complexity because vowels are often omitted in Arabic script, leading to multiple valid romanizations:

```json
{
  "DATA_SOURCE": "COMPLIANCE_INTL",
  "RECORD_ID": "INTL-40005",
  "NAME_FULL": "Mohammed Hassan Al-Shamri",
  "ADDR_FULL": "42 King Fahd Road, Riyadh, Saudi Arabia",
  "PHONE_NUMBER": "+966-11-555-0234"
}
```

```json
{
  "DATA_SOURCE": "CUSTOMERS_MENA",
  "RECORD_ID": "SA-40005",
  "NAME_FULL": "محمد حسن الشمري",
  "ADDR_FULL": "طريق الملك فهد 42، الرياض، المملكة العربية السعودية",
  "PHONE_NUMBER": "+966-11-555-0234"
}
```

Senzing's Southwest Asian cultural group handling manages the transliteration between Arabic script and Latin characters. The name "محمد حسن الشمري" maps to "Mohammed Hassan Al-Shamri", and Senzing also accounts for common romanization variants such as "Muhammad", "Mohamed", or "Mohammad" for the first name.

### Limitations of Cross-Script Matching

Cross-script matching is powerful but not infallible. There are scenarios where automatic matching may not succeed, and understanding these limitations helps you set appropriate expectations and plan for manual review where needed.

**Semantic translations vs. phonetic transliterations.** Cross-script matching works best when names are transliterated phonetically — that is, when the sounds of the name are preserved across scripts. When names are translated semantically instead (by meaning rather than sound), matching becomes unreliable. For example, the Chinese name "约翰·史密斯" is a phonetic transliteration of "John Smith", but an organization called "中國銀行" translates semantically to "Bank of China" rather than being a phonetic rendering. Senzing v4 handles CJK-to-English semantic translations for organizational names, but this capability does not extend to all script pairs.

**Rare or ambiguous transliterations.** Names with uncommon romanization schemes or highly ambiguous transliterations may not match. A name that has been romanized using an unusual or non-standard system may produce a Latin form that Senzing's matching algorithms do not associate with the original script version. This is especially common with names from languages that have multiple competing romanization standards (e.g., Wade-Giles vs. Pinyin for Chinese, or various romanization schemes for Arabic).

**Information loss in logographic-to-alphabetic conversion.** When converting from logographic scripts like Chinese to alphabetic scripts like Latin, information is inherently lost. Multiple distinct Chinese characters can produce the same Pinyin romanization — for example, several different characters all romanize to "Li". This ambiguity means that a Latin-script name may match against multiple unrelated Chinese-script names, or conversely, that a specific Chinese name may not match its intended Latin counterpart if the romanization is ambiguous.

**Names that have been Anglicized or culturally adapted.** People who move between language communities often adapt their names in ways that go beyond transliteration. A person named "محمد" (Muhammad) might use "Mike" in English-speaking contexts, or someone named "小明" (Xiaoming) might go by "Simon". These cultural adaptations cannot be resolved through transliteration alone — they require additional data attributes (date of birth, phone number, address, identification numbers) to link the records.

**Organizational names across non-CJK scripts.** While Senzing v4 supports native cross-script matching for CJK-to-English organizational names, other script combinations for organizations may still require reference data. Organizations handle name translation inconsistently — some transliterate phonetically, some translate semantically, and some rebrand entirely. For these cases, using data providers or enrichment services that supply multiple script versions of organizational names can bridge the gap.

**Insufficient supporting data.** Cross-script name matching produces the strongest results when supporting attributes (addresses, phone numbers, dates of birth, identification numbers) corroborate the match. When a name is the only attribute available and the transliteration is ambiguous, Senzing may not have enough evidence to confidently resolve the records to the same entity. In compliance and sanctions screening scenarios where names may be the primary identifier, this limitation is particularly relevant — flagging potential matches for manual review is often the appropriate approach.

When automatic matching falls short, the most effective mitigation is to enrich your data with additional attributes or to provide both native-script and romanized name versions in the same record. The more representations Senzing has to work with, the higher the likelihood of a successful cross-script match.

## Multi-Language Data Quality Best Practices

Preparing multi-language data for entity resolution requires attention to issues that do not arise with single-language, Latin-script datasets. The practices in this section help you maximize match quality when your data contains names, addresses, and other attributes in multiple languages and writing systems. These recommendations build on the general data quality principles covered in Module 5 and the [Quality Scoring Methodology](QUALITY_SCORING_METHODOLOGY.md) guide, extending them to the specific challenges of multi-language data.

### Preserve Original-Script Names

The single most important practice for multi-language data is to load names in their original script. Do not pre-transliterate or romanize names before loading them into Senzing. As described in the [Non-Latin Character Support](#non-latin-character-support) section, Senzing performs its own internal transliteration using ICU and culturally-aware matching logic. When you pre-transliterate a name, you make an irreversible choice about how to romanize it — and that choice may not match the transliteration scheme Senzing uses internally. Worse, you discard the original-script form, which eliminates Senzing's ability to match against other records that contain the name in its native script.

For example, the Chinese name "王小明" can be romanized as "Wang Xiaoming" (Pinyin), "Wong Siu Ming" (Cantonese), or other variants depending on the romanization system. If you pre-transliterate to "Wong Siu Ming" and another source provides "Wang Xiaoming", Senzing has to bridge two different romanizations — a harder problem than matching the original Chinese characters directly. Loading "王小明" as-is lets Senzing generate all relevant transliterations internally and match against any of them.

This applies equally to Arabic, Cyrillic, Devanagari, and all other non-Latin scripts. Always preserve the original-script form in your data. If your source system has already romanized the data and the original script is lost, load what you have — but recognize that matching quality may be reduced compared to having the native-script version.

### Using Multiple Name Attributes

When your source data contains both a native-script name and a romanized version, include both in the same record. This gives Senzing multiple representations to work with and improves matching accuracy. Use separate name feature objects for each version, with `NAME_TYPE` to distinguish them when the source provides that information.

Here is an example using the recommended SGES FEATURES format with both an original Chinese name and its romanized form:

```json
{
  "DATA_SOURCE": "CUSTOMERS_APAC",
  "RECORD_ID": "CN-50001",
  "FEATURES": [
    { "NAME_TYPE": "PRIMARY", "NAME_FULL": "张伟" },
    { "NAME_FULL": "Zhang Wei" },
    { "ADDR_FULL": "北京市海淀区中关村大街1号" },
    { "PHONE_NUMBER": "+86-10-5555-0789" }
  ]
}
```

In this record, the primary name is the original Chinese script "张伟", and the romanized form "Zhang Wei" is included as an additional name. Senzing uses both representations for matching: the Chinese characters match against other Chinese-script records, and the romanized form matches against Latin-script records. The `NAME_TYPE` of `PRIMARY` on the Chinese name tells Senzing to prefer that form for display purposes.

For records where the source provides an AKA (also known as) in a different script, include it as a separate name feature:

```json
{
  "DATA_SOURCE": "COMPLIANCE_INTL",
  "RECORD_ID": "INTL-50002",
  "FEATURES": [
    { "NAME_TYPE": "PRIMARY", "NAME_FULL": "Aleksandr Petrov" },
    { "NAME_TYPE": "AKA", "NAME_FULL": "Александр Петров" },
    { "DATE_OF_BIRTH": "1985-03-12" },
    { "ADDR_FULL": "15 Rue de la Paix, Paris, France" }
  ]
}
```

Key rules for multiple name attributes:

- Keep each name feature object internally consistent — do not mix `NAME_FULL` with parsed name fields (`NAME_FIRST`, `NAME_LAST`) in the same object.
- Do not mix `NAME_ORG` with parsed person name fields in the same object.
- When both parsed names and a full name are available, prefer parsed person names (`NAME_FIRST`, `NAME_LAST`) for the primary name and use `NAME_FULL` for additional script versions.
- Use `NAME_TYPE` values like `PRIMARY` and `AKA` when the source provides them. `PRIMARY` determines the best display name for the resolved entity.

### Multi-Language Data Quality Issues

Multi-language datasets introduce data quality problems that go beyond the standard issues of missing fields and inconsistent formats. These issues directly affect entity resolution accuracy and should be addressed during data preparation.

#### Inconsistent Romanization

The same name can be romanized differently depending on the system used, the country of origin, or the preferences of the person entering the data. This is one of the most common quality issues in multi-language datasets.

Examples of inconsistent romanization for the same name:

| Original Script | Romanization Variant 1 | Romanization Variant 2 | Romanization Variant 3 |
| --- | --- | --- | --- |
| 王小明 (Chinese) | Wang Xiaoming (Pinyin) | Wong Siu Ming (Cantonese) | Ong Siau Beng (Hokkien) |
| محمد (Arabic) | Muhammad | Mohammed | Mohamed |
| Александр (Cyrillic) | Aleksandr | Alexander | Alexandr |

When your data contains romanized names from multiple sources, each source may use a different romanization convention. Senzing's culturally-aware matching handles many common romanization variants — for example, it recognizes that "Muhammad", "Mohammed", and "Mohamed" are variants of the same Arabic name. However, highly divergent romanizations (such as Pinyin vs. Hokkien romanization for the same Chinese name) may not match automatically.

**What to do:** Where possible, include the original-script name alongside any romanized form. When only romanized forms are available, do not attempt to standardize them to a single romanization scheme — Senzing handles variant matching better than a manual standardization process that might introduce errors. Instead, if you know that a romanized name has an alternative spelling in another source, include both as separate name attributes on the record.

#### Mixed-Script Fields

Mixed-script fields occur when a single data field contains characters from multiple writing systems — for example, a name field containing both Latin and Chinese characters like "John 史密斯" or an address mixing Arabic and Latin text. These fields are problematic because they do not clearly belong to any single cultural group, which can interfere with Senzing's culturally-aware matching logic.

Common causes of mixed-script fields:

- Data entry systems that concatenate a romanized given name with a native-script surname (or vice versa)
- Address fields that mix a romanized street name with a native-script city or country
- Organization names that combine a Latin brand name with a native-script legal suffix

**What to do:** When possible, separate mixed-script content into distinct attributes before loading. If a name field contains "John 史密斯", split it into two name features — one with the Latin portion and one with the Chinese portion, or provide the full name in each script separately. If separation is not feasible, load the mixed-script field as-is — Senzing will process it, but matching accuracy may be lower than with clean single-script values.

#### Honorifics and Titles Across Languages

Honorifics and titles vary significantly across languages and can interfere with name matching if they are embedded in name fields inconsistently. A Japanese name might include "さん" (san) or "様" (sama), an Arabic name might include "الشيخ" (Sheikh) or "الدكتور" (Doctor), and a German name might include "Herr" or "Frau". When some records include these titles in the name field and others do not, the extra text can reduce matching confidence.

**What to do:** If your source data includes honorifics or titles as separate fields, keep them separate — do not concatenate them into `NAME_FULL`. If they are already embedded in the name field, load them as-is rather than attempting to strip them manually, which risks removing meaningful parts of the name (for example, "Al-" prefixes in Arabic names are not honorifics but part of the name). Senzing's name matching logic accounts for common titles and honorifics, but inconsistent inclusion across records can still reduce match scores. When possible, use the parsed name fields (`NAME_PREFIX` for titles, `NAME_FIRST`, `NAME_LAST` for the name itself) to keep titles separate from the name.

### How Module 5 Quality Scoring Applies to Multi-Language Data

The [Quality Scoring Methodology](QUALITY_SCORING_METHODOLOGY.md) used in Module 5 evaluates data across four dimensions: completeness (40% weight), consistency (30%), format compliance (20%), and uniqueness (10%). Each of these dimensions has specific implications for multi-language data that are worth understanding before you run your quality assessment.

#### Completeness

Completeness measures how many critical fields have actual values. Multi-language datasets often have uneven completeness across data sources — a Chinese customer database might have complete name and address fields but no email addresses, while a European source might have email and phone but sparse address data. When these sources are assessed together, the completeness score reflects the combined picture.

Multi-language data can also have a subtler completeness issue: records that contain only a romanized name without the original-script version. While these records are not technically incomplete (the name field has a value), they are missing information that would improve matching quality. The quality scorer does not penalize this directly, but you should treat "romanized name only" records as candidates for enrichment when the original-script form is available elsewhere.

#### Consistency

Consistency measures whether values in each field follow a uniform format. This is where multi-language data typically scores lowest. Phone numbers from different countries use different formats (`+86-10-5555-0123` vs. `(555) 123-4567` vs. `+966-11-555-0234`). Dates may appear as `2024-01-15` in one source and `15/01/2024` in another. Names may be in different scripts entirely — which is not an inconsistency from an entity resolution perspective (Senzing handles cross-script matching natively) but may be flagged by a format-based consistency check.

When reviewing a consistency score for multi-language data, consider whether low scores in name or address fields reflect genuine quality problems or simply the natural variation of multi-script data. A dataset containing names in Chinese, Arabic, and Latin scripts is not inconsistent — it is multilingual. Focus consistency improvement efforts on fields where format standardization is meaningful, such as phone numbers, dates, and postal codes.

#### Format Compliance

Format compliance checks whether field values pass validation rules for their expected data type. Multi-language data can trigger false negatives in format compliance checks that were designed for Latin-script data. For example, an email validation regex that only accepts ASCII characters will reject a valid internationalized email address. A phone number validator expecting North American formats will flag valid international numbers.

When your data spans multiple countries, expect format compliance scores to reflect the diversity of international formats rather than actual data quality problems. Review flagged records to distinguish between genuinely invalid values (a phone number with too few digits) and valid international formats that the validator does not recognize.

#### Uniqueness

Uniqueness measures how many records are distinct. Multi-language data introduces a specific uniqueness challenge: the same entity may appear with its name in different scripts across different sources, and these are not duplicates — they are legitimate records that Senzing should resolve to the same entity. An exact-duplicate check that compares raw field values will not flag "王小明" and "Wang Xiaoming" as duplicates, which is correct behavior. However, if the same source contains both "Wang Xiaoming" and "WANG XIAOMING" (case variation only), that is a genuine duplicate worth addressing.

The uniqueness dimension is generally the least affected by multi-language considerations, since cross-script variations are handled by Senzing's entity resolution rather than by pre-load deduplication.

## Further Reading

The Senzing documentation is the authoritative source for the latest information on multi-language support, globalization capabilities, and entity specification details. If you are using the Senzing Bootcamp through Kiro, you can query the documentation directly using the `search_docs` MCP tool.

Here are some useful queries to get started:

- `search_docs("globalization")` — Senzing's overall globalization architecture and supported languages
- `search_docs("transliteration")` — how Senzing transliterates names across writing systems
- `search_docs("cross-script matching")` — details on matching names written in different scripts
- `search_docs("multi-language")` — general multi-language entity resolution guidance
- `search_docs("entity specification")` — the full Senzing Entity Specification (SGES) attribute reference, including name and address attributes used in multi-language records
- `search_docs("name matching")` — how Senzing's name comparison algorithms work across cultural groups

Documentation evolves as Senzing adds support for new scripts, improves matching algorithms, and updates the entity specification. Use `search_docs` to get the current state rather than relying on any single point-in-time reference.
