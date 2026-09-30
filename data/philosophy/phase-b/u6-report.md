# U6 phase B test set report

## Sampling

Seed: `20261001`.

The picker in `u6-work/pick_candidates.py` excluded the Original Library, Zhuan Falun, and all three Tao Te Ching works. For each language it sampled 16 included book works and 10 included writing works without replacement, then selected one child chunk uniformly at random from each sampled work. It shuffled the 26 candidates per language after selection. The picker did not filter by text length and did not write queries. I read every candidate with its adjacent chunks before choosing targets.

Of 104 sampled candidates, 24 were not retained:

- 5 failed sampling rule 4: one English chunk consisted of translation notes rather than passage text; one Simplified Chinese chunk had only 75 characters; and three Traditional Chinese candidates had under 80 body characters after headings, dates, and audience notation were excluded.
- 1 Simplified Chinese poem extraction was corrupted and unreadable, so no honest query could be written.
- 18 candidates passed rule 4 but were left out after selecting the final 20 per language with stronger passage-specific questions and balanced work-kind coverage.

The five rule 4 candidates were `stay-rational.en-p0-c3`, `a-congratulatory-letter-to-the-fa-conference-of-taiwan.zh-Hans-p0-c1`, `teachings-at-the-2004-international-conference-in-new-york.zh-Hant-p35-c6`, `hong-yin-ii.zh-Hant-p68-c0`, and `hong-yin-iv.zh-Hant-p98-c0`. The unreadable extraction was `hong-yin-iii.zh-Hans-p26-c1`.

## Row counts

| Language | Total | Book | Writing |
|---|---:|---:|---:|
| `en` | 20 | 12 | 8 |
| `vi` | 20 | 12 | 8 |
| `zh-Hans` | 20 | 12 | 8 |
| `zh-Hant` | 20 | 12 | 8 |

For `zh-Hant`, 8 targets are from files flagged `derived`; 12 are not derived.

## Eight example rows with target text

Each excerpt below is exactly the first 300 characters of the target chunk.

### `en` example 1

Row:

```json
{"group": "en", "query": "How does a cultivation path without fixed external forms leave each practitioner responsible for shaping a different route?", "target_chunk_id": "collected-teachings-given-around-the-world-volume-x.en-p8-c5", "work_id": "collected-teachings-given-around-the-world-volume-x", "language": "en", "section_key": "collected-teachings-given-around-the-world-volume-x-s02", "language_filter": "en", "work_filter": null}
```

Target chunk (first 300 characters):

```text
at the same time, it means that it is really hard for people to look to others as a reference, except for in matters of diligence. This is something that Dafa initiated just for you, and it is something unprecedented. So this is a path you must blaze and walk for yourself. The responsibility that yo
```

### `en` example 2

Row:

```json
{"group": "en", "query": "Which sources of resolve and protection does the greeting credit with helping practitioners survive a violent effort to stop the practice?", "target_chunk_id": "to-the-canada-fa-conference.en-p0-c0", "work_id": "to-the-canada-fa-conference", "language": "en", "section_key": "to-the-canada-fa-conference-en-s01", "language_filter": "en", "work_filter": null}
```

Target chunk (first 300 characters):

```text
# to-the-canada-fa-conference-en-s01 — To the Canada Fa Conference

Master’s Recent Articles
To the Canada Fa Conference
Greetings to all Dafa disciples attending the Fa conference!
The old forces never intended for Dafa to survive the evil they forged with fire and blood. But
through the strength o
```

### `vi` example 1

Row:

```json
{"group": "vi", "query": "Bài thơ gắn việc đi qua nhiều sân khấu với phương tiện nào để truyền điều tác giả muốn nói?", "target_chunk_id": "hong-yin-v.vi-p24-c0", "work_id": "hong-yin-v", "language": "vi", "section_key": "hong-yin-v-vi-s25", "language_filter": "vi", "work_filter": null}
```

Target chunk (first 300 characters):

```text
# hong-yin-v-vi-s25 — Vì để cứu bạn trở về Thiên đường

Tôi qua lại các sân khấu trên thế giới như con thoi Để truyền đi chân tướng tôi dùng lời ca Cùng múa với Thần trải Thiên lộ Tìm về đạo đức truyền thống sẽ cao thượng Người phần nhiều từ Thiên quốc nhưng đã quên Chờ đợi Sáng Thế Chủ tạo tân vũ t
```

### `vi` example 2

Row:

```json
{"group": "vi", "query": "Đoạn này khuyên người tu nhìn khó nạn và bức hại theo nguyên nhân nào, thay vì nảy sinh oán hận?", "target_chunk_id": "stay-out-of-danger.vi-p0-c7", "work_id": "stay-out-of-danger", "language": "vi", "section_key": "stay-out-of-danger-vi-s01", "language_filter": "vi", "work_filter": null}
```

Target chunk (first 300 characters):

```text
quan không được còn sinh tâm oán hận, rằng tu luyện là tu bản thân. Tất cả những điều chư vị làm, gồm những gì đã làm và những bức hại phải nhận trong khi giảng chân tướng, là quá trình tu luyện và những điều ắt phải làm, bức hại bị cựu thế lực cưỡng chế cũng là do nghiệp lực tồn tại nơi bản thân ch
```

### `zh-Hans` example 1

Row:

```json
{"group": "zh-Hans", "query": "为何把只对少数听众讲的内容再转告别人，会让原本的讲解失去作用？", "target_chunk_id": "teachings-given-on-lantern-festival-day-2003.zh-Hans-p20-c6", "work_id": "teachings-given-on-lantern-festival-day-2003", "language": "zh-Hans", "section_key": "teachings-given-on-lantern-festival-day-2003-s02", "language_filter": "zh-Hans", "work_filter": null}
```

Target chunk (first 300 characters):

```text
一来呢，就失去了他的作用，人家听了就会不舒服。同时你讲出来还带有你的心在里边，多数是有一种显示，潜在的、潜意识的。我想今后你就不要再传这样的事了。我讲了你听了就听了。你们知道那个千年修道的人，他们得一点真机装在肚子里呀，装上千百年都不告诉别人的，（众笑）谁要想知道我这点东西还得交换哪。你们呢，突噜突噜突噜都说出来了，（笑）不装事儿。（众笑）
```

### `zh-Hans` example 2

Row:

```json
{"group": "zh-Hans", "query": "这篇短文把日常修炼和面向社会做的哪项责任并列为缺一不可？", "target_chunk_id": "a-reminder.zh-Hans-p0-c0", "work_id": "a-reminder", "language": "zh-Hans", "section_key": "a-reminder-s01", "language_filter": "zh-Hans", "work_filter": null}
```

Target chunk (first 300 characters):

```text
# a-reminder-s01 — 提醒

明慧网参加美中法会的大法弟子，大家好！大法弟子保证每天的修炼是必需的，讲真相救人是大法弟子的使命。在走向圆满的路上，
、两者缺一不可。做的如何，就是精進与否的修炼状态。社会形势会变化，修炼的要求永远不会改变，因为那是宇宙的标准，是大法的标准。祝法会圆满成功！李洪志二零一六年七月三十一日
```

### `zh-Hant` example 1

Row:

```json
{"group": "zh-Hant", "query": "修煉者初次看到的形象，講者說可能來自哪裡？", "target_chunk_id": "teachings-at-the-conference-in-switzerland.zh-Hant-p6-c4", "work_id": "teachings-at-the-conference-in-switzerland", "language": "zh-Hant", "section_key": "teachings-at-the-conference-in-switzerland-s02", "language_filter": "zh-Hant", "work_filter": null}
```

Target chunk (first 300 characters):

```text
如果你們在修煉的開始第一次看到的東西，可能是你們的原形，或者是最早所在的地方的影象，或者是人形的，或者是動物，或者是這個，或者是那個。天上的鳥也是神。弟子：修煉人能不能喫補品？師：你沒看書，就是沒看書。大家想一想，修煉的人身體有病是不能夠出功的，也就是說你不純淨的身體是不能夠修煉的。那麼你修煉的時候就要把你身體淨化下來，達到了絕對純淨的成度，然後開始出功。所以我講我們不治病。但是我會
```

### `zh-Hant` example 2

Row:

```json
{"group": "zh-Hant", "query": "這段話把修煉者能承擔常人做不到之事，連到他們必須珍視甚麼？", "target_chunk_id": "collected-fa-teachings-vol-xiii.zh-Hant-p29-c1", "work_id": "collected-fa-teachings-vol-xiii", "language": "zh-Hant", "section_key": "collected-fa-teachings-vol-xiii-s02", "language_filter": "zh-Hant", "work_filter": null}
```

Target chunk (first 300 characters):

```text
完成不了的，你能做常人做不了的事情。你是大法弟子，你有大法，你有未來的大法。可是有些人不這樣想，他沒有把這個法重視到這種成度，他沒有那麼強的正念，那就做不了，就做不好，就會一路走過來都是歪歪、扭扭。當然有些大法弟子做的那是很好。我講了，我說大法弟子根基不同嘛，有的就做的非常好，有的業力沒那麼大，它也不敢過份的迫害，有的就業力大一些，它就敢利用這個本身的業力來進行迫害。開
```
