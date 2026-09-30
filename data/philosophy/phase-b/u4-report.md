# Phase B U4 report

## Counts

- Works: 117
- Language records by status: derived: 30, included: 320, skipped: 56
- Derived records: 30
- Child chunks by language: en: 7574, vi: 17402, zh-Hans: 9174, zh-Hant: 11416
- Works by number of aligned languages: 0: 41, 2: 67, 3: 6, 4: 3

## Before and after rework

Before (the 2026-09-30 output that failed chunk quality):
- Child chunks by language: en: 7613, vi: 19203, zh-Hans: 12116, zh-Hant: 13790
- Sections by language: en: 361, vi: 5508, zh-Hans: 268, zh-Hant: 466
- Works by aligned-language count: 0: 38, 2: 68, 3: 8, 4: 3

After this rebuild:
- Child chunks by language: en: 7574, vi: 17402, zh-Hans: 9174, zh-Hant: 11416
- Sections by language: en: 344, vi: 4066, zh-Hans: 536, zh-Hant: 844
- Works by aligned-language count: 0: 41, 2: 67, 3: 6, 4: 3

## Records skipped at ingest

- `hong-yin/zh-Hans` — Every Simplified layout failed the common-character check; best candidate outside_share=0.217453.
- `hong-yin/zh-Hant` — Traditional PDF failed with outside_share=0.105882 (9/85 CJK characters), above the 10% threshold. No included Simplified edition exists in this group.
- `hong-yin-ii/zh-Hans` — Every Simplified layout failed the common-character check; best candidate outside_share=0.223390.
- `hong-yin-iii/en` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `hong-yin-iv/zh-Hans` — Every Simplified layout failed the common-character check; best candidate outside_share=0.983235.
- `hong-yin-v/zh-Hans` — Every Simplified layout failed the common-character check; best candidate outside_share=0.262570.
- `to-the-dafa-disciples-attending-the-conference-in-taiwan/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `greetings-to-the-european-fa-conference/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `to-the-czecho-slovak-fa-conference/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `to-the-2021-dafa-conference-in-taiwan/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `wake-up/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `a-strong-and-urgent-warning/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `to-the-fa-conference-in-germany/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `greetings-to-the-taiwan-fa-conference/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `on-the-general-election/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `another-stern-warning/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `stay-rational/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `congratulatory-letter/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `dafa-disciples-are-fulfilling-their-missions/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `greetings-to-the-south-america-fa-conference/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `greetings-to-the-dafa-disciples-attending-the-fa-conference-of-europe/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `to-the-fa-conference-in-france/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `to-the-canada-fa-conference/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `to-the-practitioners-of-vietnam/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `to-the-experience-sharing-conference-in-taiwan/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `to-the-2018-asia-fa-conference/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `to-the-fa-conference-of-europe/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `on-falun-dafas-classification-in-the-ordinary-world/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `a-congratulatory-letter-to-the-european-fa-conference-in-paris/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `to-the-fa-conference-in-japan/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `creating-anew/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `a-congratulatory-letter-to-the-fa-conference-of-argentina/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `a-congratulatory-letter-to-the-fa-conference-of-taiwan/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `a-greeting-to-the-south-america-fa-conference/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `on-the-responses-to-the-piece-about-assistant-souls/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `a-reminder/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `tian-guo-marching-band/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `on-dafa/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `still-so-arrogant-and-reckless/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `the-red-demon-is-incinerated-while-adamantine-ones-are-tempered/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `righteous-thoughts/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `congratulations-to-the-taiwan-fa-conference/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `stay-clearheaded/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `to-choose/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `giang-phap-tai-phap-hoi-new-york-2019/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `phap-hoi-tan-duong-nhan-va-dai-ky-nguyen-nam-2018/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `giang-phap-tai-washington-dc-nam-2018/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `giang-phap-tai-phap-hoi-new-york-ky-niem-25-nam-dai-phap-hong-truyen/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `giang-phap-tai-phap-hoi-new-york-2016/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `giang-phap-tai-phap-hoi-mien-tay-my-quoc-2015/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `giang-phap-tai-phap-hoi-new-york-2015/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `giang-phap-tai-phap-hoi-san-francisco-2014/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `giang-phap-ngay-phap-luan-dai-phap-the-gioi/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `giang-phap-o-phap-hoi-quoc-te-mien-tay-my-quoc-nam-2013/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `giang-phap-o-phap-hoi-tai-vung-do-thi-new-york-nam-2013/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body
- `giang-phap-tai-phap-hoi-quoc-te-o-thu-do-my-quoc-2012/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body

## Works whose language sections did not align

- `falun-gong` — en: 31, vi: 3, zh-Hans: 14, zh-Hant: 14
- `further-discussions-on-falun-dafa` — en: 2, vi: 5, zh-Hans: 5, zh-Hant: 5
- `explaining-the-teachings-of-zhuan-falun` — en: 6, vi: 5, zh-Hans: 6, zh-Hant: 6
- `zhuan-falun-volume-ii` — en: 24, vi: 25, zh-Hans: 17, zh-Hant: 17
- `lecture-given-at-the-conference-in-sydney` — en: 1, vi: 3, zh-Hans: 2, zh-Hant: 1
- `the-great-way-of-spiritual-perfection` — en: 2, vi: 7, zh-Hans: 50, zh-Hant: 50
- `teachings-at-conferences-in-the-united-states` — en: 3, vi: 2, zh-Hans: 3, zh-Hant: 3
- `essentials-for-further-advancement` — en: 71, vi: 79, zh-Hans: 80, zh-Hant: 80
- `teachings-at-the-first-conference-in-north-america` — en: 1, vi: 1, zh-Hans: 2, zh-Hant: 2
- `teachings-at-the-conference-in-europe` — en: 1, vi: 1, zh-Hans: 2, zh-Hant: 1
- `teachings-at-the-conference-of-changchun-assistants` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `teachings-at-the-conference-in-singapore` — en: 1, vi: 1, zh-Hans: 2, zh-Hant: 2
- `teachings-at-the-conference-in-switzerland` — en: 1, vi: 1, zh-Hans: 3, zh-Hant: 3
- `hong-yin` — en: 12, vi: 447, zh-Hans: 0, zh-Hant: 0
- `teachings-at-the-conference-in-the-western-u-s` — en: 1, vi: 1, zh-Hans: 3, zh-Hant: 3
- `teachings-at-the-conference-in-the-eastern-u-s` — en: 1, vi: 1, zh-Hans: 2, zh-Hant: 2
- `teachings-at-the-conference-in-australia` — en: 1, vi: 1, zh-Hans: 2, zh-Hant: 2
- `teachings-at-the-conference-in-new-zealand` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `teachings-at-the-conference-in-canada` — en: 1, vi: 1, zh-Hans: 2, zh-Hant: 2
- `teachings-at-the-midwestern-u-s-conference` — en: 1, vi: 1, zh-Hans: 2, zh-Hant: 2
- `the-essentials-of-diligent-progress-ii` — en: 31, vi: 45, zh-Hans: 18, zh-Hant: 18
- `teachings-from-a-tour-of-north-america` — en: 1, vi: 1, zh-Hans: 2, zh-Hant: 2
- `teachings-given-on-lantern-festival-day-2003` — en: 1, vi: 1, zh-Hans: 2, zh-Hant: 2
- `hong-yin-ii` — en: 9, vi: 547, zh-Hans: 0, zh-Hant: 84
- `teachings-at-the-conference-in-houston` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `collected-teachings-given-around-the-world-volume-ii` — en: 2, vi: 5, zh-Hans: 4, zh-Hant: 4
- `teaching-the-fa-at-the-discussion-on-writing-music-and-creating-fine-art` — en: 1, vi: 1, zh-Hans: 2, zh-Hant: 2
- `collected-teachings-given-around-the-world-volume-iv` — en: 4, vi: 2, zh-Hans: 3, zh-Hant: 3
- `collected-teachings-given-around-the-world-volume-v` — en: 2, vi: 2, zh-Hans: 3, zh-Hant: 3
- `collected-teachings-given-around-the-world-volume-vi` — en: 3, vi: 2, zh-Hans: 2, zh-Hant: 2
- `teachings-at-the-2004-international-conference-in-new-york` — en: 1, vi: 1, zh-Hans: 2, zh-Hant: 2
- `collected-teachings-given-around-the-world-volume-vii` — en: 3, vi: 3, zh-Hans: 4, zh-Hant: 4
- `teachings-at-the-2005-conference-in-san-francisco` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `teachings-at-the-conference-in-los-angeles` — en: 1, vi: 1, zh-Hans: 2, zh-Hant: 1
- `hong-yin-iii` — en: 0, vi: 100, zh-Hans: 90, zh-Hant: 124
- `the-essentials-of-diligent-progress-iii` — en: 25, vi: 59, zh-Hans: 60, zh-Hant: 60
- `collected-teachings-given-around-the-world-volume-viii` — en: 4, vi: 1, zh-Hans: 3, zh-Hant: 3
- `collected-teachings-given-around-the-world-volume-ix` — en: 3, vi: 3, zh-Hans: 2, zh-Hant: 3
- `collected-teachings-given-around-the-world-volume-x` — en: 4, vi: 3, zh-Hans: 4, zh-Hant: 4
- `collected-teachings-given-around-the-world-volume-xi` — en: 4, vi: 2, zh-Hans: 4, zh-Hant: 4
- `hong-yin-iv` — en: 1, vi: 1473, zh-Hans: 0, zh-Hant: 99
- `hong-yin-v` — en: 1, vi: 1135, zh-Hans: 0, zh-Hant: 98
- `collected-fa-teachings-vol-xii` — en: 4, zh-Hans: 5, zh-Hant: 4
- `collected-fa-teachings-vol-xiii` — en: 3, zh-Hans: 5, zh-Hant: 3
- `collected-fa-teachings-vol-xiv` — en: 2, zh-Hans: 3, zh-Hant: 1
- `collected-fa-teachings-vol-xv` — en: 7, zh-Hans: 5, zh-Hant: 5
- `hong-yin-vi` — en: 1, vi: 61, zh-Hans: 58, zh-Hant: 58
- `why-shen-yun-can-save-lives` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `critical-times-reveal-ones-spiritual-state` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `our-practice-and-the-term-religion` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `why-this-world-is-a-realm-of-unknowing` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `a-wake-up-call` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `the-ordeals-our-spiritual-discipline-faces` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `to-the-dafa-disciples-attending-the-conference-in-taiwan` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `how-you-should-regard-and-act-toward-masters-family-members` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `dafa-spiritual-practice-is-serious` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `stay-out-of-danger` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `to-the-european-fa-conference` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `to-the-italy-fa-conference` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `to-the-india-fa-conference` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `why-the-creator-seeks-to-save-all-life` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `how-humankind-came-to-be` — en: 1, vi: 1, zh-Hans: 1, zh-Hant: 1
- `greetings-to-the-european-fa-conference` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `to-the-2021-dafa-conference-in-taiwan` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `wake-up` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `a-strong-and-urgent-warning` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `to-the-fa-conference-in-germany` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `greetings-to-the-taiwan-fa-conference` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `another-stern-warning` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `stay-rational` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `congratulatory-letter` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `dafa-disciples-are-fulfilling-their-missions` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `greetings-to-the-south-america-fa-conference` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `greetings-to-the-dafa-disciples-attending-the-fa-conference-of-europe` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `to-the-fa-conference-in-france` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `to-the-canada-fa-conference` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `to-the-practitioners-of-vietnam` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `to-the-experience-sharing-conference-in-taiwan` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `to-the-2018-asia-fa-conference` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `to-the-fa-conference-of-europe` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `on-falun-dafas-classification-in-the-ordinary-world` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `a-congratulatory-letter-to-the-european-fa-conference-in-paris` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `to-the-fa-conference-in-japan` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `a-congratulatory-letter-to-the-fa-conference-of-argentina` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `a-congratulatory-letter-to-the-fa-conference-of-taiwan` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `a-congratulatory-letter-to-the-fa-conference-of-europe` — en: 1, zh-Hans: 1, zh-Hant: 1
- `a-greeting-to-the-south-america-fa-conference` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `on-the-responses-to-the-piece-about-assistant-souls` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `a-reminder` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `congratulations-to-the-taiwan-fa-conference` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1
- `stay-clearheaded` — en: 1, vi: 0, zh-Hans: 1, zh-Hant: 1

## Six work samples

### collected-teachings-given-around-the-world-volume-i (book; multi-up source)

| # | en | vi | zh-Hans | zh-Hant |
|---:|---|---|---|---|
| 1 | Teaching the Fa at the Founding Ceremony of the Singaporean Falun Dafa Association | Giảng Pháp tại Lễ thành lập Phật học hội Singapore | 新加坡佛学会成立典礼讲法 | 新加坡佛學會成立典禮講法 |
| 2 | First Fa Teaching Given in the United States | Giảng Pháp lần thứ nhất tại Mỹ quốc | 美国第一次讲法 | 美國第一次講法 |
| 3 | Teaching the Fa at the International Experience-Sharing Conference in Beijing | Giảng Pháp tại Hội giao lưu Quốc tế tại Bắc Kinh | 北京国际交流会讲法 | 北京國際交流會講法 |

Chunk excerpts (first and last child for the first and last available section):

- `en` / Teaching the Fa at the Founding Ceremony of the Singaporean Falun Dafa Association: first `collected-teachings-given-around-the-world-volume-i.en-p0-c0`: # collected-teachings-given-around-the-world-volume-i-s01 — Teaching the Fa at the Founding Ceremony of the Singaporean Falun Dafa Association Hongzhi Li July 28, 1996 ~ Singapore All right, let me just stand here and let everyone see me clearly. I’d like to thank the people from various fields in S
  last `collected-teachings-given-around-the-world-volume-i.en-p7-c1`: will find that it is a book about true cultivation. As you keep reading it, you will find that it is a divine book. With the same sentence, you will have different understandings and different interpretations at different levels and in different realms. There is an enormous amount of meaning in the 
- `en` / Teaching the Fa at the International Experience-Sharing Conference in Beijing: first `collected-teachings-given-around-the-world-volume-i.en-p17-c0`: # collected-teachings-given-around-the-world-volume-i-s03 — Teaching the Fa at the International Experience-Sharing Conference in Beijing Hongzhi Li November 2, 1996 ~ Beijing I know your feelings, and I miss you, too. But I can tell you this: as long as you diligently cultivate yourself, I am const
  last `collected-teachings-given-around-the-world-volume-i.en-p22-c6`: and without interference from demons, you couldn’t eliminate karma. This is the truth. Humans, objects, and living beings all have these two features. Humans are formed by both Buddha-nature and demon-nature. When you are cultivating yourself with Buddhist principles, you are actually getting rid of
- `vi` / Giảng Pháp tại Lễ thành lập Phật học hội Singapore: first `collected-teachings-given-around-the-world-volume-i.vi-p0-c0`: # collected-teachings-given-around-the-world-volume-i-s01 — Giảng Pháp tại Lễ thành lập Phật học hội Singapore Lý Hồng Chí Ngày 28 tháng 7 năm 1996 Được rồi, tôi cứ đứng ở đây nhé, để mọi người nhìn được rõ. Cảm ơn các nhân sỹ các nơi tại Singapore đã ủng hộ Pháp Luân Phật học hội về mọi phương diện
  last `collected-teachings-given-around-the-world-volume-i.vi-p16-c5`: sẽ phát sinh vấn đề mới, khi chư vị lại xem tiếp lần thứ ba, tất cả những vấn đề này của chư vị lại đều sẽ được giải đáp. Vậy thì tiếp tục xem vẫn sẽ phát sinh những vấn đề cao hơn, chỉ cần chư vị không ngừng đọc sách, thì đều sẽ giải đáp cho chư vị. Không biết những điều tôi giảng có hợp với khẩu v
- `vi` / Giảng Pháp tại Hội giao lưu Quốc tế tại Bắc Kinh: first `collected-teachings-given-around-the-world-volume-i.vi-p34-c0`: # collected-teachings-given-around-the-world-volume-i-s03 — Giảng Pháp tại Hội giao lưu Quốc tế tại Bắc Kinh Lý Hồng Chí Ngày 2 tháng 11 năm 1996 Tôi biết tâm tình của mọi người, tôi cũng rất nhớ mọi người. Nhưng tôi bảo chư vị, chỉ cần chư vị tu luyện cho tốt, thì tôi luôn luôn ở bên cạnh chư vị. R
  last `collected-teachings-given-around-the-world-volume-i.vi-p47-c0`: # collected-teachings-given-around-the-world-volume-i-s03 — Giảng Pháp tại Hội giao lưu Quốc tế tại Bắc Kinh bất hoặc tức là không còn mơ hồ nữa, chín chắn rồi, không bị lầm lạc nữa
- `zh-Hans` / 新加坡佛学会成立典礼讲法: first `collected-teachings-given-around-the-world-volume-i.zh-Hans-p0-c0`: # collected-teachings-given-around-the-world-volume-i-s01 — 新加坡佛学会成立典礼讲法 李洪志一九九六年七月二十八日好，我就站在这儿吧，给大家看清楚。谢谢新加坡方方面面给予法轮佛学会支持的各方人士，我也代表大家对新加坡给予我们支持、能够成立法轮佛学会的各方面人士致谢，大家给鼓鼓掌。（鼓掌）佛学会的成立会使更多的人得法，会使更多的有缘人能够学到这个法，在国家法律的保障中，对今后大家炼功，更好的为广大的民众做这件好事，提供了一个方便条件。没做过多的准备，下面，我就借这次大会的机会，想到哪，讲到
  last `collected-teachings-given-around-the-world-volume-i.zh-Hans-p12-c0`: # collected-teachings-given-around-the-world-volume-i-s01 — 新加坡佛学会成立典礼讲法 看一万遍，你都不会觉的没有什么可看的了，反而你还会发现还有许许多多你没体会到的东西，你还会有许许多多新的领会，所以这本书是相当珍贵的。我不可能面面俱到的在这里都讲出来，如果你能够修炼，我想，你就认真的把他学下去，反复的看，你就什么都能得。你第一遍看出来的问题，你再看第二遍书的时候你所有的问题都会得到解答。那么你会产生新的问题，你再看第三遍的时候，你所有这些问题又都会得到解答。那么再看还会产生更高的问题，你只要不断的看书，都会给你解答。不知道我讲的合不
- `zh-Hans` / 北京国际交流会讲法: first `collected-teachings-given-around-the-world-volume-i.zh-Hans-p27-c0`: # collected-teachings-given-around-the-world-volume-i-s03 — 北京国际交流会讲法 李洪志一九九六年十一月二日，北京我知道大家的心情，我也很想念大家。不过我告诉你们，只要你好好修炼，我时时都在你们的身边。很多学员修的很好，我也知道。许多学员处于开悟的前夕。在最近一个时期我跟许多学员讲过这样的话，我说得这个法很不容易。可能有的人觉的我只是听到了消息，或者朋友告诉我，偶然看到这本书，或者是在报纸上得到的消息，我就来了，从此以后就走入了大法修炼的这条路。其实你别看很简单，你别看表面上得这个法好象是很轻而易举，因为很少会出现来
  last `collected-teachings-given-around-the-world-volume-i.zh-Hans-p35-c2`: 疯狂了一样，和妖魔有什么不同呀？男人留着很长很怪的头发，男不男、女不女的，说什么艺术家、音乐家的形像，其实都是魔性带动下的心理变态。有道德约束的人那才是佛性。什么是修佛？就是要去你的魔性，都同化成佛性。我刚才讲的东西很高，甚至于很具体了。我就讲这么多了。 （长时间热烈鼓掌）
- `zh-Hant` / 新加坡佛學會成立典禮講法: first `collected-teachings-given-around-the-world-volume-i.zh-Hant-p0-c0`: # collected-teachings-given-around-the-world-volume-i-s01 — 新加坡佛學會成立典禮講法 李洪志一九九六年七月二十八日好，我就站在這兒吧，給大家看清楚。謝謝新加坡方方面面給予法輪佛學會支持的各方人士，我也代表大家對新加坡給予我們支持、能夠成立法輪佛學會的各方面人士致謝，大家給鼓鼓掌。（鼓掌）佛學會的成立會使更多的人得法，會使更多的有緣人能夠學到這個法，在國家法律的保障中，對今後大家煉功，更好的為廣大的民眾做這件好事，提供了一個方便條件
  last `collected-teachings-given-around-the-world-volume-i.zh-Hant-p14-c5`: 領會，所以這本書是相當珍貴的。我不可能面面俱到的在這裏都講出來，如果你能夠修煉，我想，你就認真的把他學下去，反覆的看，你就甚麼都能得。你第一遍看出來的問題，你再看第二遍書的時候你所有的問題都會得到解答。那麼你會產生新的問題，你再看第三遍的時候，你所有這些問題又都會得到解答。那麼再看還會產生更高的問題，你只要不斷的看書，都會給你解答。不知道我講的合不合大家的口味。（鼓掌）盼大家修
- `zh-Hant` / 北京國際交流會講法: first `collected-teachings-given-around-the-world-volume-i.zh-Hant-p31-c0`: # collected-teachings-given-around-the-world-volume-i-s03 — 北京國際交流會講法 一九九六年十一月二日，北京北京國際交流會講法李洪志一九九六年十一月二日，北京我知道大家的心情，我也很想念大家。不過我告訴你們，只要你好好修煉，我時時都在你們的身邊。很多學員修的很好，我也知道。許多學員處於開悟的前夕。在最近一個時期我跟許多學員講過這樣的話，我說得這個法很不容易。可能有的人覺的我只是聽到了消息，或者朋友告訴我，偶然看到這本書，或者是在報紙上得到的消息，我就來了，從此以後就走
  last `collected-teachings-given-around-the-world-volume-i.zh-Hant-p41-c1`: 念的發揮，像瘋狂了一樣，和妖魔有甚麼不同呀？男人留著很長很怪的頭髮，男不男、女不女的，說甚麼藝術家、音樂家的形像，其實都是魔性帶動下的心理變態。有道德約束的人那才是佛性。甚麼是修佛？就是要去你的魔性，都同化成佛性。我剛才講的東西很高，甚至於很具體了。我就講這麼多了。 （長時間熱烈鼓掌）

### why-the-creator-seeks-to-save-all-life (writing)

| # | en | vi | zh-Hans | zh-Hant |
|---:|---|---|---|---|
| 1 | Why the Creator Seeks to Save All Life | Tại sao muốn cứu độ chúng sinh | 为什么要救度众生 | 為甚麼要救度眾生 |

Chunk excerpts (first and last child for the first and last available section):

- `en` / Why the Creator Seeks to Save All Life: first `why-the-creator-seeks-to-save-all-life.en-p0-c0`: Why does the Creator seek to save all lives? It is because of His love for them, and because it is He who bestowed them with life. During this final phase of the cosmos’s Formation, Stasis, Degeneration, and Destruction cycle, the Creator spent 200 million years making the Three Realms as well as pl
  last `why-the-creator-seeks-to-save-all-life.en-p0-c2`: all divine beings in the Cosmos. He is the maker of the Lord of lords, of the King of kings, and He is the Sovereign of all lives—including the Three Realms’ human lives, spiritual beings, and material things, all of which He made. His love is the highest and most sacred blessing for all lives! Ther
  Only one section was extracted for `en`.
- `vi` / Tại sao muốn cứu độ chúng sinh: first `why-the-creator-seeks-to-save-all-life.vi-p0-c0`: Bài viết của Sư phụ Lý Hồng Chí Tại sao muốn cứu độ chúng sinh Vì sao Sáng Thế Chủ muốn cứu độ chúng sinh! Bởi vì Ngài yêu thương chúng sinh! Vì sinh mệnh của chúng sinh đều do Ngài ban cho. Khi Thiên thể trong Thành, Trụ, Hoại, Diệt tới bước cuối cùng, Sáng Thế Chủ đã dùng thời gian 200 triệu năm t
  last `why-the-creator-seeks-to-save-all-life.vi-p0-c4`: vật trong Tam giới mà Ngài tạo ra. Tình yêu của Ngài là thánh ân tối cao đối với chúng sinh! Được Ngài yêu thương là vinh hạnh lớn nhất của con người! Sư phụ: Lý Hồng Chí Ngày 17 tháng 4 năm 2023 (Cập nhật ngày 5 tháng 8 năm 2024)
  Only one section was extracted for `vi`.
- `zh-Hans` / 为什么要救度众生: first `why-the-creator-seeks-to-save-all-life.zh-Hans-p0-c0`: 创世主为什么要救度众生！因为他爱众生！因为众生的生命都是他给予的。当天体在成住坏灭到了末后时，创世主用两亿年的时间造了三界，为众生安排得救的、、、各种形式与机缘，同时奠定了人的文化与思想行为他还用自己的神体为众生消解罪业！为救众。生他付出了自己的一切。为了末后在开启救度时人能达到神的要求，两亿年中创世主无数分身转生在世上铺垫人类文化，看守人类道德在历史漫长的岁月中，生命轮回辗转千万年的往复等待，渐渐世人的
  last `why-the-creator-seeks-to-save-all-life.zh-Hans-p0-c2`: 爱的人。。那是他的权利，谁都无权干涉！那是他对生命的无上恩典！创世主是天体中一切神的主，他是万主之主，万王之王的造就者，一切众生的主宰，包括他造的三界中的一切人神物他的爱是对众生最高的圣恩！世人被他所爱是人最大的荣幸！ 、、。师李洪志二零二三年四月十七日简体字A4版：PDF文件简体字Letter版：PDF文件正体字A4版：PDF文件
  Only one section was extracted for `zh-Hans`.
- `zh-Hant` / 為甚麼要救度眾生: first `why-the-creator-seeks-to-save-all-life.zh-Hant-p0-c0`: 創世主為甚麼要救度眾生！因為他愛眾生！因為眾生的生命都是他給予的。當天體在成、住、壞、滅到了末後時，創世主用兩億年的時間造了三界，為眾生安排得救的各種形式與機緣，同時奠定了人的文化與思想行為。他還用自己的神體為眾生消解罪業！為救眾生他付出了自己的一切。為了末後在開啟救度時人能達到神的要求，兩億年中創世主無數分身轉生在世上鋪墊人類文化，看
  last `why-the-creator-seeks-to-save-all-life.zh-Hant-p0-c2`: 救度世人鋪墊神的文化，留下的各類正教也是在為維護人類道德而存在，等待創世主最後的救度。對於創世主來說，他有權愛他的人，他也會更愛他認為可愛的人。那是他的權利，誰都無權干涉！那是他對生命的無上恩典！創世主是天體中一切神的主，他是萬主之主，萬王之王的造就者，一切眾生的主宰，包括他造的三界中的一切人、神、物。他的愛是對眾生最高的聖恩！世人被他所愛是人最大的榮幸！
  Only one section was extracted for `zh-Hant`.

### guiding-the-voyage (book; derived Traditional Chinese, multi-up source)

| # | en | vi | zh-Hans | zh-Hant |
|---:|---|---|---|---|
| 1 | Fa Teaching Given at the Western U.S. Fa Conference | Giảng Pháp tại Pháp hội miền Tây Mỹ quốc | 北美大湖区法会讲法 | 北美大湖區法會講法 |
| 2 | Fa Teaching Given at the 2001 Canada Fa Conference | Giảng Pháp tại Pháp hội Canada năm 2001 | 二零零一年加拿大法会讲法 | 二零零一年加拿大法會講法 |

Chunk excerpts (first and last child for the first and last available section):

- `en` / Fa Teaching Given at the Western U.S. Fa Conference: first `guiding-the-voyage.en-p0-c0`: # guiding-the-voyage-s01 — Fa Teaching Given at the Western U.S. Fa Conference Hongzhi Li October 21, 2000 ~ San Francisco, U.S.A. It’s been a long time! (Applause) Alright, let’s hold the applause and hear what I have to say. When any being in this cosmos has enlightened to his own Way and principl
  last `guiding-the-voyage.en-p5-c4`: There’s sacredness in them that you know now and sacredness in them that you don’t know. You can’t sense how magnificent they are from the way they manifest among ordinary humans, because I can’t let you feel conceited or complacent. As your master, I can only have you try harder and take every step
- `en` / Fa Teaching Given at the 2001 Canada Fa Conference: first `guiding-the-voyage.en-p6-c0`: # guiding-the-voyage-s02 — Fa Teaching Given at the 2001 Canada Fa Conference Hongzhi Li May 19, 2001 ~ Ottawa, Canada Hello everyone! (Applause) First, I would like to wish this conference of ours complete success. (Applause) As Dafa disciples, you know that this is different from any cultivation o
  last `guiding-the-voyage.en-p10-c5`: But no matter what you do, you need to be worthy of being called a Dafa disciple. That’s as much as I’ll say today. Your sharing experiences and understandings is important, too. Under any circumstance, in any period, and no matter how busy you are with your work, you can’t stray from your Fa study,
- `vi` / Giảng Pháp tại Pháp hội miền Tây Mỹ quốc: first `guiding-the-voyage.vi-p0-c0`: # guiding-the-voyage-s01 — Giảng Pháp tại Pháp hội miền Tây Mỹ quốc Lý Hồng Chí, ngày 21 tháng 10 năm 2000 ở San Francisco Đã lâu rồi! (Vỗ tay) Được rồi, bây giờ chúng ta không vỗ tay nữa, nghe Thầy giảng. Bất kể một sinh mệnh nào trong vũ trụ này, bất luận là tại tầng thứ nào chứng ngộ được Pháp củ
  last `guiding-the-voyage.vi-p13-c3`: mọi người điều gì đó, đặc biệt là trong loại tình huống hiện nay. Cho nên tương lai tôi sẽ tìm thời gian nói cho mọi người kỹ lưỡng, hôm nay giảng bấy nhiêu thôi. Hy vọng mọi người trong việc Chính Pháp và việc phơi bày tà ác này làm được tốt hơn nữa, đó cũng là đang trong tu luyện. Giảng bấy nhiêu 
- `vi` / Giảng Pháp tại Pháp hội Canada năm 2001: first `guiding-the-voyage.vi-p14-c0`: # guiding-the-voyage-s02 — Giảng Pháp tại Pháp hội Canada năm 2001 Lý Hồng Chí, ngày 19 tháng 5 năm 2001 Chào tất cả! (vỗ tay) Trước hết xin chúc đại hội của chúng ta lần này thành công viên mãn. (vỗ tay). Là cá nhân đệ tử Đại Pháp, mọi người đã biết, việc này khác xa với bất kể việc tu luyện nào tr
  last `guiding-the-voyage.vi-p25-c4`: hối hận. [x]Chính đại khung: chỉnh lại gầm trời to lớn. [xi]Tâm đắc thể hội: những điều mà tự tâm thể mình gặp được, kinh nghiệm. Bản dịch tháng 8-2001, có thể được chỉnh sửa trong tương lai. Xin đọc giả thỉnh thoảng quay lại kiểm tra.
- `zh-Hans` / 北美大湖区法会讲法: first `guiding-the-voyage.zh-Hans-p0-c0`: # guiding-the-voyage-s01 — 北美大湖区法会讲法 我看到大家很高兴。在一年前你们不是这样，经过这样严峻的考验，可能你们没有那么大的感觉，我却看到你们完全不是原来的这个人了。我们大家都经历了历史上从来没有过的、最严厉的考核，而且是邪恶的。过去我们无论做任何事情，大家都在想：我要怎么样学好法，我怎么样为大法做工作，我怎么样能够提高，我怎么样能够做的更好；总感觉是在学大法，而不是身在大法当中的一员。经过了这一年以后，我发现大家完全变了，你们没有了原来的那种想法。无论为大法做什么，无论你在干什么，你们都
  last `guiding-the-voyage.zh-Hans-p8-c0`: # guiding-the-voyage-s01 — 北美大湖区法会讲法 关于那些具体的问题，我想有机会呢，找时间跟大家去讲。不是每一个法会我都能参加，我每次出来都是有目地的，不是随随便便的跟大家去讲什么，特别是在现在这种情况下。所以将来我会找时间详细的跟大家谈，今天就不讲那么多了。希望大家在正法这件事情与揭露邪恶这件事情上做的更好，这也是在修炼其中。就讲这么多，谢谢大家。（鼓掌）
- `zh-Hans` / 二零零一年加拿大法会讲法: first `guiding-the-voyage.zh-Hans-p9-c0`: # guiding-the-voyage-s02 — 二零零一年加拿大法会讲法 二零零一年五月十九日于渥太华大家好！（鼓掌）
  last `guiding-the-voyage.zh-Hans-p17-c4`: 一个大法弟子做大法的事，因为你们的圆满是主要的，你们的圆满在你们现在来说就是第一位的。当然你们的圆满中也溶着你们对大法的负责、普度众生。我告诉大家，你们都在讲师父在普度众生，你们都圆满了，回过头来你们就看到了你们当时普度的众生。讲清真相中，你们就在救度着众生。我就讲这么多，下面你们的会接着开始。
- `zh-Hant` / 北美大湖區法會講法: first `guiding-the-voyage.zh-Hant-p0-c0`: # guiding-the-voyage-s01 — 北美大湖區法會講法 我看到大家很高興。在一年前你們不是這樣，經過這樣嚴峻的考驗，可能你們沒有那麼大的感覺，我卻看到你們完全不是原來的這個人了。我們大家都經歷了歷史上從來沒有過的、最嚴厲的考覈，而且是邪惡的。過去我們無論做任何事情，大家都在想：我要怎麼樣學好法，我怎麼樣爲大法做工作，我怎麼樣能夠提高，我怎麼樣能夠做的更好；總感覺是在學大法，而不是身在大法當中的
  last `guiding-the-voyage.zh-Hant-p8-c1`: 關於那些具體的問題，我想有機會呢，找時間跟大家去講。不是每一個法會我都能參加，我每次出來都是有目地的，不是隨隨便便的跟大家去講什麼，特別是在現在這種情況下。所以將來我會找時間詳細的跟大家談，今天就不講那麼多了。希望大家在正法這件事情與揭露邪惡這件事情上做的更好，這也是在修煉其中。就講這麼多，謝謝大家。（鼓掌）
- `zh-Hant` / 二零零一年加拿大法會講法: first `guiding-the-voyage.zh-Hant-p9-c0`: # guiding-the-voyage-s02 — 二零零一年加拿大法會講法 二零零一年五月十九日於渥太華大家好！（鼓掌）
  last `guiding-the-voyage.zh-Hant-p19-c6`: 常人要幫做大法的事，當然那是好事，但我這裏是指大法弟子，你們必須得是一個大法弟子做大法的事，因爲你們的圓滿是主要的，你們的圓滿在你們現在來說就是第一位的。當然你們的圓滿中也溶着你們對大法的負責、普度衆生。我告訴大家，你們都在講師父在普度衆生，你們都圓滿了，回過頭來你們就看到了你們當時普度的衆生。講清真相中，你們就在救度着衆生。我就講這麼多，下面你們的會接着開始。

### why-shen-yun-can-save-lives (writing)

| # | en | vi | zh-Hans | zh-Hant |
|---:|---|---|---|---|
| 1 | Why Shen Yun Can Save Lives | Thần Vận vì sao có thể cứu người | 神韵为什么能救人 | 神韻為甚麼能救人 |

Chunk excerpts (first and last child for the first and last available section):

- `en` / Why Shen Yun Can Save Lives: first `why-shen-yun-can-save-lives.en-p0-c0`: Many people wonder why people like us, who lead spiritual lives, created a performing arts company. And they want to know how it’s related to our spiritual practice. I would like to address this by saying a few words about the significance of Shen Yun. Shen Yun Performing Arts, by all appearances, i
  last `why-shen-yun-can-save-lives.en-p0-c2`: grounded. Those who aren’t on board with it are certainly free to leave at any time—as spiritual discipline is a solemn thing and it has to be done with the utmost sincerity. The divine regard what we are doing as the right thing for people on a sacred path to do. And I know for sure that it’s what 
  Only one section was extracted for `en`.
- `vi` / Thần Vận vì sao có thể cứu người: first `why-shen-yun-can-save-lives.vi-p0-c0`: Bài viết của Sư phụ Lý Hồng Chí Thần Vận vì sao có thể cứu người Nhiều người hỏi: “Vì sao người tu luyện lập đoàn nghệ thuật? Có mối quan hệ gì với bản thân tu luyện?” . Vì thế, tôi muốn nói đôi lời về ý nghĩa của Thần Vận. Kỳ thực, trên tầng diện nhân loại, Đoàn Nghệ thuật Thần Vận là đang triển hi
  last `why-shen-yun-can-save-lives.vi-p0-c4`: rằng: những gì chúng ta đang làm là những gì mà người trên đường trở thành Thần nên làm. Tôi đương nhiên biết rõ, đây chính là điều mà tôi và các đệ tử tu luyện nên làm (người ta cũng coi chúng ta là đoàn thể tôn giáo), đã làm được một việc đại thiện mà các tôn giáo khác chưa làm được. Đó cũng là mụ
  Only one section was extracted for `vi`.
- `zh-Hans` / 神韵为什么能救人: first `why-shen-yun-can-save-lives.zh-Hans-p0-c0`: 很多人问为什么修炼人搞艺术团？和修炼本身的关系是什么？为此我向大家说几句神韵的意义所在其实，神韵艺术团在人的层面上表现的是在向现代人展现传统文化，同时传递传统文化。的美好，而在高于人的层面上是更辉煌的救人展现神认为神韵艺术团这是在救人因为人是神。。造的，最终是要叫人上天堂而现代人却忘记了传统，忘记了人在传统文化中的善良，人与人之。间互敬互爱互助等美好的一切，和传统的人际关系如果人在无善无德的
  last `why-shen-yun-can-save-lives.zh-Hans-p0-c2`: 做的事，这是人通往天国必须的条件。之一当然神韵的演员（包括见习演员）都必须是修炼人，管理上除演出排练外，都必须要学法。炼功遵守修炼要求等，是个能修炼的人，做不到的当然可以随时离开，因为修炼是严肃的、。众神都这样认为：我们所做的是走在神路上的人应该做的我当然知道这是我与我的弟子修。炼人应做的（人们也认为我们作为宗教团体），做了一件其它宗教都没做到的大好事这也是我。组建神韵艺术团的目的。师李洪志二
  Only one section was extracted for `zh-Hans`.
- `zh-Hant` / 神韻為甚麼能救人: first `why-shen-yun-can-save-lives.zh-Hant-p0-c0`: 很多人問為甚麼修煉人搞藝術團？和修煉本身的關係是甚麼？為此我向大家說幾句神韻的意義所在。其實，神韻藝術團在人的層面上表現的是在向現代人展現傳統文化，同時傳遞傳統文化的美好，而在高於人的層面上是更輝煌的救人展現。神認為神韻藝術團這是在救人。因為人是神造的，最終是要叫人上天堂。而現代人卻忘記了傳統，忘記了人在傳統文化中的善良
  last `why-shen-yun-can-save-lives.zh-Hant-p0-c3`: 為：我們所做的是走在神路上的人應該做的。我當然知道這是我與我的弟子修煉人應做的（人們也認為我們作為宗教團體），做了一件其它宗教都沒做到的大好事。這也是我組建神韻藝術團的目的。師李洪志二零二五年十月六日簡體字A4版：PDF文件簡體字Letter版：PDF文件正體字A4版：PDF文件
  Only one section was extracted for `zh-Hant`.

### collected-teachings-given-around-the-world-volume-iii (book; derived Traditional Chinese, multi-up source)

| # | en | vi | zh-Hans | zh-Hant |
|---:|---|---|---|---|
| 1 | Fa Teaching Given at the Metropolitan New York Fa Conference | Giảng Pháp tại Pháp hội vùng đô thị New York | 大纽约地区法会讲法 | 大紐約地區法會講法 |
| 2 | Fa Teaching Given at the 2003 Midwest U.S. Fa Conference | Giảng Pháp tại Pháp hội miền Trung Mỹ quốc năm 2003 | 二零零三年美中法会讲法 | 二零零三年美中法會講法 |

Chunk excerpts (first and last child for the first and last available section):

- `en` / Fa Teaching Given at the Metropolitan New York Fa Conference: first `collected-teachings-given-around-the-world-volume-iii.en-p0-c0`: # collected-teachings-given-around-the-world-volume-iii-s01 — Fa Teaching Given at the Metropolitan New York Fa Conference the gaps in your xinxing anymore. At present there are some frictions among students, and you all need to watch out—you can’t let minor things affect the important things that D
  last `collected-teachings-given-around-the-world-volume-iii.en-p15-c6`: China or outside the Mainland, I hope that all of you seize the final moments to do well and do even better. Especially those of you who haven’t done well, you should seize the day and do well. Don’t let the opportunity slip by. Once the persecution ends and once the strength of the evil is no longe
- `en` / Fa Teaching Given at the 2003 Midwest U.S. Fa Conference: first `collected-teachings-given-around-the-world-volume-iii.en-p16-c0`: # collected-teachings-given-around-the-world-volume-iii-s02 — Fa Teaching Given at the 2003 Midwest U.S. Fa Conference persecution there are, from all times and all lands. The evil is out of tricks. Looking at the current situation, even though Dafa disciples and I have experienced this period of hi
  last `collected-teachings-given-around-the-world-volume-iii.en-p20-c3`: in the human world is pretty calm. But in other dimensions the influence is huge, and the impact is huge. Every time you have an event there’s a big battle between good and evil in the heavens. Of course, the evil has become less and less now, and it’s as if they’re being swept away. But of course, 
- `vi` / Giảng Pháp tại Pháp hội vùng đô thị New York: first `collected-teachings-given-around-the-world-volume-iii.vi-p0-c0`: # collected-teachings-given-around-the-world-volume-iii-s01 — Giảng Pháp tại Pháp hội vùng đô thị New York Lý Hồng Chí Ngày 20 tháng 4 năm 2003 Chào tất cả! (vỗ tay) Mọi người thật vất vả. (vỗ tay) Giai đoạn thời gian gần đây mọi người có thể đã [nhận] thấy rằng, thông qua nỗ lực không ngừng của các
  last `collected-teachings-given-around-the-world-volume-iii.vi-p36-c0`: # collected-teachings-given-around-the-world-volume-iii-s01 — Giảng Pháp tại Pháp hội vùng đô thị New York là “610”; tổ chức tai tiếng này có quyền hành rất lớn, hoạt động trên cả luật pháp, tương tự Gestapo năm xưa. ▪Điều 23: một dự luật với danh nghĩa “chống lật đổ”, nhưng quy định quá rộng, quá l
- `vi` / Giảng Pháp tại Pháp hội miền Trung Mỹ quốc năm 2003: first `collected-teachings-given-around-the-world-volume-iii.vi-p37-c0`: # collected-teachings-given-around-the-world-volume-iii-s02 — Giảng Pháp tại Pháp hội miền Trung Mỹ quốc năm 2003 Lý Hồng Chí Ngày 22 tháng 6 năm 2003 Chào tất cả! (vỗ tay nhiệt liệt) Chúng ta lần này có thể nói đúng là một hội lớn rồi đó, (vỗ tay nhiệt liệt) số học viên cũng rất nhiều. Như mọi ngườ
  last `collected-teachings-given-around-the-world-volume-iii.vi-p47-c3`: Đại Giác Giả trong tương lai, (Sư phụ cười) vào lúc cuối cùng chứng thực Pháp này hãy kiến lập uy đức lớn nhất của chư vị! (nhiệt liệt vỗ tay thời gian lâu) ● ● ● ● ● ● ● ● ● Chú thích của người dịch.(không phải chính văn, chỉ để tham khảo) Dịch ngày 27-8-2003; bản dịch có thể được chỉnh sửa trong t
- `zh-Hans` / 大纽约地区法会讲法: first `collected-teachings-given-around-the-world-volume-iii.zh-Hans-p0-c0`: # collected-teachings-given-around-the-world-volume-iii-s01 — 大纽约地区法会讲法 李洪志二零零三年四月二十日大家好！（鼓掌）
  last `collected-teachings-given-around-the-world-volume-iii.zh-Hans-p27-c3`: 但是这件事情出现了，那么给你们带来的损失，你们得自己去弥补。我希望每个大法弟子不要把形式看的太重，你自己的修炼、你自己的提高，你在邪恶中证实法、救度众生，你坚定的走好你自己应该走的路才是最重要的。（鼓掌） 谢谢大家。（长时间鼓掌）
- `zh-Hans` / 二零零三年美中法会讲法: first `collected-teachings-given-around-the-world-volume-iii.zh-Hans-p28-c0`: # collected-teachings-given-around-the-world-volume-iii-s02 — 二零零三年美中法会讲法 我们这次可以说是一个盛会了啊，（热烈鼓掌）学员人数也比较多。大家都看到了，回想起来呀，从一九九九年的“七·二零”以后一直到今天，我们走过了一个时间并不算太长但是感觉却非常漫长的一段岁月，大家在这段时间里经历的太多太多了。宇宙中前所未有的一切都在小小的人世上聚焦着，旧势力在宇宙中为干扰正法所安排的一切都在这里运作着，为法而来的、为法而成的、为法而造就的，都在这段时间中展现出来了。尤其中国大陆的学员，经历了前所未有的迫害，而在这场迫
  last `collected-teachings-given-around-the-world-volume-iii.zh-Hans-p35-c3`: 战。当然，现在这个邪恶越来越少了，好象在扫除一样。当然只要邪恶它还存在，它就会起破坏作用，我们一定要不能掉以轻心，还要配合的更好，多多的沟通。走好大法弟子最后的路吧。更多的话以后还会讲，客气话呀、赞扬话呀我也不想多说。因为大家都是大法弟子，师父讲什么事都是开门见山。这次会上也就不多讲了，因为一会儿大家还要吃饭。（长时间热烈鼓掌） 未来的大觉者们，（师笑）在最后的证实法中建立你们的最大的威德吧！
- `zh-Hant` / 大紐約地區法會講法: first `collected-teachings-given-around-the-world-volume-iii.zh-Hant-p0-c0`: # collected-teachings-given-around-the-world-volume-iii-s01 — 大紐約地區法會講法 李洪志二零零三年四月二十日大家好！（鼓掌）
  last `collected-teachings-given-around-the-world-volume-iii.zh-Hant-p30-c5`: 情已經出現了，不出現呢也就無所謂了。師父什麼都能做、什麼都能歸正，但是這件事情出現了，那麼給你們帶來的損失，你們得自己去彌補。我希望每個大法弟子不要把形式看的太重，你自己的修煉、你自己的提高，你在邪惡中證實法、救度衆生，你堅定的走好你自己應該走的路纔是最重要的。（鼓掌） 謝謝大家。（長時間鼓掌）
- `zh-Hant` / 二零零三年美中法會講法: first `collected-teachings-given-around-the-world-volume-iii.zh-Hant-p31-c0`: # collected-teachings-given-around-the-world-volume-iii-s02 — 二零零三年美中法會講法 我們這次可以說是一個盛會了啊，（熱烈鼓掌）學員人數也比較多。大家都看到了，回想起來呀，從一九九九年的“七·二零”以後一直到今天，我們走過了一個時間並不算太長但是感覺卻非常漫長的一段歲月，大家在這段時間裏經歷的太多太多了。宇宙中前所未有的一切都在小小的人世上聚焦着，舊勢力在宇宙中爲干擾正法所安排的一切都在這裏運作着，爲法而來的、爲法而成的、爲法而造就的，都在這段
  last `collected-teachings-given-around-the-world-volume-iii.zh-Hant-p39-c3`: 弟子，師父講什麼事都是開門見山。這次會上也就不多講了，因爲一會兒大家還要喫飯。（長時間熱烈鼓掌） 未來的大覺者們，（師笑）在最後的證實法中建立你們的最大的威德吧！ （長時間熱烈鼓掌）

### to-the-italy-fa-conference (writing)

| # | en | vi | zh-Hans | zh-Hant |
|---:|---|---|---|---|
| 1 | To the Italy Fa Conference | Gửi Pháp hội Italy | 意大利法会 | 意大利法會 |

Chunk excerpts (first and last child for the first and last available section):

- `en` / To the Italy Fa Conference: first `to-the-italy-fa-conference.en-p0-c0`: # to-the-italy-fa-conference-en-s01 — To the Italy Fa Conference July 23, 2023 To the Italy Fa Conference: I would like to extend my greetings to the Dafa practitioners attending the Fa conference in Italy. The Dafa disciples of the Fa-rectification period all have a mission to assist Master in savi
  last `to-the-italy-fa-conference.en-p0-c0`: # to-the-italy-fa-conference-en-s01 — To the Italy Fa Conference July 23, 2023 To the Italy Fa Conference: I would like to extend my greetings to the Dafa practitioners attending the Fa conference in Italy. The Dafa disciples of the Fa-rectification period all have a mission to assist Master in savi
  Only one section was extracted for `en`.
- `vi` / Gửi Pháp hội Italy: first `to-the-italy-fa-conference.vi-p0-c0`: Bài viết của Sư phụ Lý Hồng Chí Gửi Pháp hội Italy Gửi Pháp hội Italy: Chào tất cả các học viên Đại Pháp tham dự Pháp hội Italy. Các đệ tử Đại Pháp thời kỳ Chính Pháp đều có sứ mệnh trợ Sư cứu người. Các đệ tử Đại Pháp của các địa phương đều trở thành hy vọng cho những người tại địa phương đó được c
  last `to-the-italy-fa-conference.vi-p0-c0`: Bài viết của Sư phụ Lý Hồng Chí Gửi Pháp hội Italy Gửi Pháp hội Italy: Chào tất cả các học viên Đại Pháp tham dự Pháp hội Italy. Các đệ tử Đại Pháp thời kỳ Chính Pháp đều có sứ mệnh trợ Sư cứu người. Các đệ tử Đại Pháp của các địa phương đều trở thành hy vọng cho những người tại địa phương đó được c
  Only one section was extracted for `vi`.
- `zh-Hans` / 意大利法会: first `to-the-italy-fa-conference.zh-Hans-p0-c0`: # to-the-italy-fa-conference-s01 — 意大利法会 参加意大利法会的大法学员大家好正法时期的大法弟子都有助师救人的使命那各个地区的大。。法弟子就成为了所在地区人们得救的希望为此我们必须修好自己承担起这前所未有的最伟大的。使命与责任，多学法，早日成熟起来，助师救众生！祝法会圆满！师李洪志二零二三年七月二十三日简体字A4版：PDF文件简体字Letter版：PDF文件正体字A4版：PDF文件
  last `to-the-italy-fa-conference.zh-Hans-p0-c0`: # to-the-italy-fa-conference-s01 — 意大利法会 参加意大利法会的大法学员大家好正法时期的大法弟子都有助师救人的使命那各个地区的大。。法弟子就成为了所在地区人们得救的希望为此我们必须修好自己承担起这前所未有的最伟大的。使命与责任，多学法，早日成熟起来，助师救众生！祝法会圆满！师李洪志二零二三年七月二十三日简体字A4版：PDF文件简体字Letter版：PDF文件正体字A4版：PDF文件
  Only one section was extracted for `zh-Hans`.
- `zh-Hant` / 意大利法會: first `to-the-italy-fa-conference.zh-Hant-p0-c0`: # to-the-italy-fa-conference-s01 — 意大利法會 參加意大利法會的大法學員大家好。正法時期的大法弟子都有助師救人的使命。那各個地區的大法弟子就成為了所在地區人們得救的希望。為此我們必須修好自己承擔起這前所未有的最偉大的使命與責任，多學法，早日成熟起來，助師救眾生！祝法會圓滿！師李洪志二零二三年七月二十三日簡體字A4版：PDF文件簡體字Letter版：PDF文件正體字A4版：PDF文件
  last `to-the-italy-fa-conference.zh-Hant-p0-c0`: # to-the-italy-fa-conference-s01 — 意大利法會 參加意大利法會的大法學員大家好。正法時期的大法弟子都有助師救人的使命。那各個地區的大法弟子就成為了所在地區人們得救的希望。為此我們必須修好自己承擔起這前所未有的最偉大的使命與責任，多學法，早日成熟起來，助師救眾生！祝法會圓滿！師李洪志二零二三年七月二十三日簡體字A4版：PDF文件簡體字Letter版：PDF文件正體字A4版：PDF文件
  Only one section was extracted for `zh-Hant`.

## Volume I section titles in all four languages

| # | en | vi | zh-Hans | zh-Hant |
|---:|---|---|---|---|
| 1 | Teaching the Fa at the Founding Ceremony of the Singaporean Falun Dafa Association | Giảng Pháp tại Lễ thành lập Phật học hội Singapore | 新加坡佛学会成立典礼讲法 | 新加坡佛學會成立典禮講法 |
| 2 | First Fa Teaching Given in the United States | Giảng Pháp lần thứ nhất tại Mỹ quốc | 美国第一次讲法 | 美國第一次講法 |
| 3 | Teaching the Fa at the International Experience-Sharing Conference in Beijing | Giảng Pháp tại Hội giao lưu Quốc tế tại Bắc Kinh | 北京国际交流会讲法 | 北京國際交流會講法 |


## Reading-order excerpts

The following are three child chunks around the midpoint of each file; each excerpt is capped at 400 characters.

### Five Simplified 2合1 files

#### `collected-teachings-given-around-the-world-volume-i.zh-Hans` — source `2合1__gb_book_0028_844895432b__g01.pdf`
- `collected-teachings-given-around-the-world-volume-i.zh-Hans-p18-c0`: # collected-teachings-given-around-the-world-volume-i-s02 — 美国第一次讲法 喜欢这个法走入政治，也不能让他進入政治。修炼的东西一旦進入政治就是邪法，我们只是在民间流传着，没有通过正式的报纸呀，甚至于没有公开的大力宣传，都是修炼者觉的好自己告诉别人来学的。一个人觉的好就叫家里人也来学。大家知道，如果自己觉的不怎么样他不会叫家里人来学。家里人觉的好，亲朋好友、亲戚他都叫来学了，就是在民间这样传开了。我也是从最低层次开始讲的，逐渐的讲高，这么讲呀讲了两年，最后真正讲大法又讲了两年，一共是四年时间，在中国几乎
- `collected-teachings-given-around-the-world-volume-i.zh-Hans-p18-c1`: 快家喻户晓。在国外影响也是很大的，尽管人还没有修炼，可是很多人都听说过了。在东南亚影响可能比美国就大一些，有许多国家也成立了辅导站，成立了法轮大法佛法学会、法轮大法学会，是呈现一种快速上升的趋势。这里我告诉大家一件事情，现在用释迦牟尼的话讲是末法时期不行了的时候，就是没有法了，释迦牟尼讲他的法到了末法时期就不能度人了。当然有许多和尚也是修炼不成的了，因为他也不知道怎么修了，对经书中的理解也不行了，认识不到经书中的真正的涵义了
- `collected-teachings-given-around-the-world-volume-i.zh-Hans-p18-c2`: ，所以就很难修了。现在学的人很多，我告诉大家，人类社会出现什么状态都不是偶然的。有着那么多人来学，是不是没有这种天象也就不会出现呢？我告诉大家，保证它是有原因的。人类有相生相克的理，有正的出现一定也有邪的出现。那么另外一方面就是，当今社会各种邪教呀、大量的假气功呀，表面上干这些事的人为了钱、要出名，其实很多可能是邪魔转生乱世。释迦牟尼讲他传法的时候看到人类社会“五毒俱全”。其实现在的社会比那个时候的要复杂的多，是十恶俱全

#### `collected-teachings-given-around-the-world-volume-vii.zh-Hans` — source `2合1__gb_book_0036_ad18f17ea7__g01.pdf`
- `collected-teachings-given-around-the-world-volume-vii.zh-Hans-p18-c1`: 须放手大事、小事都得管的作风。各地充份发挥地区学员主动证实法的事要支持，不要限制，除非经常走极端的之外，老的大法弟子都成熟了，他们都在走自己圆满的路，要清楚。弟子：东欧的学员是否应该退党和退团？师：世人都要对这表态，但是目前不是很主要。东欧恶党毕竟解体了。如果那里有人现在还是坚定恶党信徒，那就会同样被清除。中共是恶党邪灵最后的主体，救度中国人就是解体恶党的邪灵。弟子：我感到西方学员认为《九评》是华人学员的事。您能
- `collected-teachings-given-around-the-world-volume-vii.zh-Hans-p18-c2`: 否给予开示？师：主要是华人学员，这是没有问题的。但是世人都得表态，而且西方有许多人也对中共恶党这个认识不清。世人说法轮功了不起还包括几层涵义在里面。其中一个问题是，一百多年来，这个共产集团社会和自由社会的互相之间一直在斗争，而且一直那么激烈，冷战时期好象随时都有打原子战争的危险，也没有人能说清中共邪党是什么。谁说清了？只不过是互相在对骂。有那么多研究这个恶党的人与组织也没有研究清楚它是个什么东西来。国民党
- `collected-teachings-given-around-the-world-volume-vii.zh-Hans-p18-c3`: 和中共打了几十年，也没说清楚中共恶党是什么。法轮功把这个恶党说清楚了，这不是很了不起吗？这不令世人刮目相看吗？为什么常人社会有很多人佩服大法弟子啊？人类的很多事情是常人根本说不清的。大法弟子能把其说清楚，这就是了不起。不只是西方社会，全人类都没有认清邪党是什么。大家现在急于解决的是救度被毒害最深的中国人，叫中国人看清中共恶党。但是西方也有许多人也对邪党认识不清，也有极少数人甚至是拥护邪党的，那对他们来

#### `collected-fa-teachings-vol-xii.zh-Hans` — source `2合1__gb_book_0047_740e4c1fff__g01.pdf`
- `collected-fa-teachings-vol-xii.zh-Hans-p21-c3`: 一个原因就是有的人心太强了嘛。我都讲过了，集体做事时，谁的主意也不可能是最完善的，社会是千变万化，形势还在变化呢，人还有一个今天这个时髦明天那个时髦呢。这是一个动的社会，不要追求自己的主意怎么好。只要能完成这件事情，大家就努力去做了。你觉的哪方面不完善，你把它做完善，这才是了不起的，这才是神愿意看到的，这才是修炼人应该做的。（鼓掌）而不是哪个意见、谁的意见怎么圆满了不起，你把它争来了，那恰恰是神反对的，
- `collected-fa-teachings-vol-xii.zh-Hans-p21-c4`: 师父也不愿意看到的。而且旧势力觉的越不圆满越好，你去做吧，漏洞百出，谁能把它补上那才了不起，给了大家共同修炼的机会，它是这么看的。弟子：有些同修专职在几个媒体做，没有生活来源。有的媒体发一点生活补助，钱都是学员捐的。有同修悟到拿补贴不符合师父讲的开工资的法，就离开了媒体，去常人中找了一份工作，选择了其它的讲真相项目。弟子也面临拿补贴的问题，对此怎么认识？师父：有的媒体拿补贴是我同
- `collected-fa-teachings-vol-xii.zh-Hans-p21-c5`: 意的，要想尽快把媒体公司做好，你没有收入怎么行？不专职做怎么能行？初期可以这样。你比如说，新唐人现在要从新把它做好，这个期间出于这种情况可以，但是不会长，现负责人也不会让这个事情太长。

#### `collected-fa-teachings-vol-xiii.zh-Hans` — source `2合1__gb_book_0048_dba8c7d8d4__g01.pdf`
- `collected-fa-teachings-vol-xiii.zh-Hans-p26-c3`: 五度角的方向，每个方向分出许多枝杈等等手势）它出来那一个杈上还有这个。那纵向的呢？（师父边说边做在垂直于身体、高于腰部一些的某个水平面上向正前方延伸的手势）这样的呢？（师父做手势示意该平面上与正前方呈四十五度角的方向）这样的呢？（师父做手势示意该平面上与正前方呈负四十五度角的方向）这样的呢？（师父在身体前、平行于身体的平面上做十二点钟方向的手势）这样的呢？（师父边说边双手在该平面上做一点半、十点半方
- `collected-fa-teachings-vol-xiii.zh-Hans-p27-c0`: # collected-fa-teachings-vol-xiii-zh-Hans-s04 — 二零一五年纽约法会讲法 （师父在与水平面呈四十五度角的某平面上示意一点半、十点半方向，每个方向又分别分出许多枝杈的等等手势）它都有杈，杈上还有杈。我说的就是分子构成的这个空间它就复杂到这种成度。能看到的也只是肉眼通。肉眼通开的层次也不一样，你看到的互相之间也可能都不一样。生命的奥秘呀，真的是非常壮观，不是象现在人类的技术所能看到的那一点点。人要想在技术的这条路上往前走，永远都是在爬行啦。但是不管怎么样，我刚才讲，我就说这意思，人类，包括
- `collected-fa-teachings-vol-xiii.zh-Hans-p27-c1`: 大法弟子，在修炼当中，都是在很窄的这条路上在做。它有一个好处，就说，那以外的哪，我做错了我不知道。人的生命就是这样的。不然的话，那种干扰，那各种复杂的因素啊，你根本就没办法。人的智慧也是有限的。在这样一条窄的路上做，你就能够容易的面对你所碰到的这些问题。我过去讲，人在世上做什么，其它时空中无数的生命都在看着你。有的人不相信。常人不相信没有关系，作为大法弟子知道，其实人的那个思想念头，高层生命看的很清楚，怎么样思维的都看的见。

#### `collected-fa-teachings-vol-xiv.zh-Hans` — source `2合1__gb_book_0049_4dc6ed3bcd__g01.pdf`
- `collected-fa-teachings-vol-xiv.zh-Hans-p18-c6`: 师父：如果赞扬他把贪官坏人抓起来，这应该没问题的。其它做法，常人的事情你不要去随便赞扬，也不要随便去管。弟子：个别西人学员由此对大纪元的真实性产生怀疑。师父：就象我刚才讲的，我们是来救人的，不是搞政治斗争的。对中国那些领导人也好，其他人也一样，一概都打，不行的，我们是来救人的。没有迫害法轮功的，相反的，把劳教所给取消了，劳教所是啥地方？专门迫害大法弟子。把
- `collected-fa-teachings-vol-xiv.zh-Hans-p19-c0`: # collected-fa-teachings-vol-xiv-zh-Hans-s02 — 法輪大法 “六一零”的头子都给抓起来了，当然是以腐败份子抓的，不管以什么方式做的都是好事，不是为法轮功做的。那旧势力说，以法轮功名义做，那这事不就完了吗？就停止了吗？停止不就结束了吗？是。以这个方式做，既能够敲醒人，又能让人感觉迫害法轮功这是报应，又能够对大法弟子讲真相有利，人做了于大法有利的事情、做了对救人有利的事情。不能够去攻击没迫害大法弟子的人。（众鼓掌）
- `collected-fa-teachings-vol-xiv.zh-Hans-p19-c1`: 弟子：四年以来泰文网站缺乏更新，包括新的《论语》还没有放到网上，但是泰国学员翻译新经文很及时。有关方面是否能够重视并更好的协调？师父：是。大法弟子做的事情要注意，要做就象样的去做啊。弟子：最近一段时间有某台湾学员来泰国，建议泰国学员讲真相时应该讲创世主。师父：又乱来了。讲真相的事情没有变！弟子：我在德国得法，来到土耳其。土耳其当地学法之后不交流，说自己悟，感觉没有成为一个整体。在德国，大家敞开交流。师父：是，看到问题就跟他

### Five previously letter-spaced Traditional files

#### `hong-yin-ii.zh-Hant` — vertical spans 14983/15260; rotated pages 52/53; derived: False
- `hong-yin-ii.zh-Hant-p41-c0`: # hong-yin-ii-zh-Hant-s42 — 天又清 天昏昏地暗暗神雷炸陰霾散橫掃亂法爛鬼別說慈悲心淡二零零二年六月十六日寫給美國中部法會
- `hong-yin-ii.zh-Hant-p42-c0`: # hong-yin-ii-zh-Hant-s43 — 詩：震懾 神筆震人妖快刀爛鬼消舊勢不敬法揮毫滅狂濤二零零二年七月二十八日
- `hong-yin-ii.zh-Hant-p43-c0`: # hong-yin-ii-zh-Hant-s44 — 詩：快講 大法徒講真相口中利劍齊放揭穿爛鬼謊言抓緊救度快講二零零二年八月二十一日五○

#### `hong-yin-iv.zh-Hant` — vertical spans 0/1897; rotated pages 0/153; derived: False
- `hong-yin-iv.zh-Hant-p59-c0`: # hong-yin-iv-zh-Hant-s60 — 真實的理 朋友神不願放棄你不是因為你有甚麼了不起那是對生命的慈悲真相會告訴你謎底對大法的抹黑會被清洗謊言毒害的是你的心裏身體的創傷可以治癒中毒的生命會在大難中解體我只想叫你看清善惡我想告訴你生命真實的理二零一三年冬
- `hong-yin-iv.zh-Hant-p60-c0`: # hong-yin-iv-zh-Hant-s61 — 大海是我的胸懷 大海是我的胸懷藍天下都是我的舞臺助師救人是我的誓約傳真相是神的安排甘露遍撒大地民舍宮宅千萬年的等待沒有白挨創世主已來魔難中大法徒在全力救世人狂徒腳下卻是懸崖我們雖然沉冤不白紅潮托起的是千古英才因為我們走向神的未來二零一三年冬
- `hong-yin-iv.zh-Hant-p61-c0`: # hong-yin-iv-zh-Hant-s62 — 詩：救度 宇宙最後一頁已經翻啟救度中神叫我喚醒你別看我們被抹黑真相會把一切清洗謊言毒害卻在你的心裏肉體的傷害可以治癒中毒的生命將在紅朝末日中解體我只想叫你分辨善惡選擇由你自己我只想叫你了解真相因為你曾經求神別把你放棄二零一四年一月一日

#### `hong-yin-v.zh-Hant` — vertical spans 0/1833; rotated pages 0/125; derived: False
- `hong-yin-v.zh-Hant-p49-c0`: # hong-yin-v-zh-Hant-s50 — 神路在身旁 神路通天堂大法在洪揚人為此事來金錢把路擋不信神來世真相在身旁名利情如幻錯過悔斷腸人生事無常來去一身光神叫把你喚渡船快起航二零一五年十月二十三日
- `hong-yin-v.zh-Hant-p50-c0`: # hong-yin-v-zh-Hant-s51 — 識途是聖賢 天路在眼前為何看不見來世千百年尋路從未閒名利迷人眼末世少善念幾人能醒悟識途是聖賢二零一五年十月二十四日
- `hong-yin-v.zh-Hant-p51-c0`: # hong-yin-v-zh-Hant-s52 — 幾人醒 人間再好事無常聖潔美好在天堂榮華百年帶不走名利拼搏為誰忙人多神來太久長等創世主再救亡消去罪業塑神體你的天國迎新王二零一六年

#### `hong-yin-vi.zh-Hant` — vertical spans 0/868; rotated pages 0/91; derived: False
- `hong-yin-vi.zh-Hant-p28-c0`: # hong-yin-vi-s29 — 踏上渡船 我們從天體深處走來助創世主救人上舞台這是神聖的使命這是無量生靈的期待世人多是神轉世被迷埋等他救度回天把生命洗白現代觀念行為是毒癌不信神難得救末後化塵埃名利情離世不能帶踏上渡船生命不再苦挨踏上渡船回天出迷霾二零一九年八月二十四日
- `hong-yin-vi.zh-Hant-p29-c0`: # hong-yin-vi-s30 — 放下人心神道顯 遙遠的期盼遠古的誓言輪迴輾轉一生生滄海桑田重變換花開花落人們盼著機緣月圓了又圓人們等著回天末後創世主來傳大法這就是眾生來世的宿願世風日下找真相結聖緣放下人心神道你才看得見二零一九年八月二十四日
- `hong-yin-vi.zh-Hant-p30-c0`: # hong-yin-vi-s31 — 執迷者迷 天高地遠水長流萬古攸攸為誰留道說道理佛說法誰知創世有因由二零一九年八月二十五日

#### `lecture-given-at-the-conference-in-sydney.zh-Hant` — vertical spans 44358/44483; rotated pages 51/52; derived: False
- `lecture-given-at-the-conference-in-sydney.zh-Hant-p17-c7`: 反正要對你負責任我才講出這個道理，因為你想修，我就告訴你，不然的話等於是我沒有對你負責任。你有這樣的機緣，坐在這裏，我就告訴你。任何一門現在都很難修成了，沒有人管了，關鍵是都是亂修。當然你要自己能把握住了，你自己去修，你
- `lecture-given-at-the-conference-in-sydney.zh-Hant-p18-c0`: # lecture-given-at-the-conference-in-sydney-zh-Hant-s01 — 法輪大法悉尼法會講法 覺的能修成圓滿，在哪一門修都好，就是這樣的道理，因為佛就是為人好，所以我要告訴大家，你想修煉你就要專一。不但要動作上不能煉其它的東西，你也不能念其它的那門的經，你思想中也不能夠產生那一門的東西，意念都得去掉的。因為煉功很多東西是靠意念的，你的意念出來就是追求，你就想要那個東西，那個東西就會來。那麼，你身上的功就亂了，法輪會變形、失效，你就白修。我告訴大家：這個法輪可
- `lecture-given-at-the-conference-in-sydney.zh-Hant-p18-c1`: 太珍貴了，你別看我把他給你了，我沒傳這個東西之前，千年修道的人都想得他而得不到。得到之後，這個人可以說他修煉成一半了。功自動就會被法輪演化，只要修你的心，就會長功，提高上來。他是個高級生命，也就是說，他比你的生命還高級。你別看我給了你，是因為你要修煉，是佛性表現出來了。出這一念就度你，就這樣做了，你得到的東西是相當珍貴的。修佛可是個非常嚴肅的事情，我們也不會叫你把他禍亂了，

The sampled Traditional PDFs include two rotated vertical text layouts (Hong Yin II and the Sydney lecture); Hong Yin IV, V, and VI use horizontal text. The vertical spans are reassembled by column before sectioning. No internal Han-character spacing remains within the sampled child bodies.

## Shortest and longest chunk files

### 10 shortest
- `a-congratulatory-letter-to-the-european-fa-conference-in-paris.en.json` — 1 chunks
- `a-congratulatory-letter-to-the-european-fa-conference-in-paris.zh-Hans.json` — 1 chunks
- `a-congratulatory-letter-to-the-european-fa-conference-in-paris.zh-Hant.json` — 1 chunks
- `a-congratulatory-letter-to-the-fa-conference-of-argentina.en.json` — 1 chunks
- `a-congratulatory-letter-to-the-fa-conference-of-argentina.zh-Hans.json` — 1 chunks
- `a-congratulatory-letter-to-the-fa-conference-of-taiwan.en.json` — 1 chunks
- `a-greeting-to-the-south-america-fa-conference.en.json` — 1 chunks
- `a-greeting-to-the-south-america-fa-conference.zh-Hans.json` — 1 chunks
- `a-greeting-to-the-south-america-fa-conference.zh-Hant.json` — 1 chunks
- `a-reminder.en.json` — 1 chunks

### 10 longest

- `hong-yin-iv.vi.json` — 1489 chunks
- `hong-yin-v.vi.json` — 1161 chunks
- `explaining-the-teachings-of-zhuan-falun.vi.json` — 600 chunks
- `explaining-the-teachings-of-zhuan-falun.zh-Hant.json` — 560 chunks
- `hong-yin-ii.vi.json` — 549 chunks
- `falun-gong.vi.json` — 548 chunks
- `further-discussions-on-falun-dafa.vi.json` — 529 chunks
- `teachings-given-on-lantern-festival-day-2003.vi.json` — 494 chunks
- `explaining-the-teachings-of-zhuan-falun.zh-Hans.json` — 480 chunks
- `hong-yin.vi.json` — 448 chunks

## Source text and extraction notes

- `falun-gong/en` — removed 2 detected contents page(s).
- `falun-gong/vi` — removed 2 detected contents page(s).
- `falun-gong/vi` — removed 1 short title/cover page(s) before body text.
- `falun-gong/zh-Hans` — removed 3 detected contents page(s).
- `falun-gong/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `falun-gong/zh-Hant` — Traditional source `primary__big5_book_0002_b9ff56186b__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.940569 (4827/5132 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `further-discussions-on-falun-dafa/en` — removed 1 detected contents page(s).
- `further-discussions-on-falun-dafa/en` — removed 4 short title/cover page(s) before body text.
- `further-discussions-on-falun-dafa/vi` — removed 1 detected contents page(s).
- `further-discussions-on-falun-dafa/zh-Hans` — removed 3 detected contents page(s).
- `further-discussions-on-falun-dafa/zh-Hans` — removed 3 short title/cover page(s) before body text.
- `further-discussions-on-falun-dafa/zh-Hant` — Traditional source `primary__big5_book_0003_3f6bb2ad78__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.956910 (5041/5268 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `explaining-the-teachings-of-zhuan-falun/en` — removed 1 detected contents page(s).
- `explaining-the-teachings-of-zhuan-falun/en` — removed 1 short title/cover page(s) before body text.
- `explaining-the-teachings-of-zhuan-falun/vi` — removed 1 detected contents page(s).
- `explaining-the-teachings-of-zhuan-falun/zh-Hans` — removed 3 detected contents page(s).
- `explaining-the-teachings-of-zhuan-falun/zh-Hans` — removed 4 short title/cover page(s) before body text.
- `explaining-the-teachings-of-zhuan-falun/zh-Hant` — removed 2 detected contents page(s).
- `explaining-the-teachings-of-zhuan-falun/zh-Hant` — removed 3 short title/cover page(s) before body text.
- `zhuan-falun-volume-ii/en` — removed 1 detected contents page(s).
- `zhuan-falun-volume-ii/vi` — removed 1 detected contents page(s).
- `zhuan-falun-volume-ii/vi` — removed 1 short title/cover page(s) before body text.
- `zhuan-falun-volume-ii/zh-Hans` — removed 3 detected contents page(s).
- `zhuan-falun-volume-ii/zh-Hans` — removed 3 short title/cover page(s) before body text.
- `zhuan-falun-volume-ii/zh-Hant` — Traditional source `primary__big5_book_0005_18aad402bc__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.951076 (1944/2044 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `lecture-given-at-the-conference-in-sydney/zh-Hans` — removed 2 detected contents page(s).
- `lecture-given-at-the-conference-in-sydney/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `lecture-given-at-the-conference-in-sydney/zh-Hant` — removed 1 detected contents page(s).
- `lecture-given-at-the-conference-in-sydney/zh-Hant` — removed 2 short title/cover page(s) before body text.
- `the-great-way-of-spiritual-perfection/en` — removed 1 detected contents page(s).
- `the-great-way-of-spiritual-perfection/en` — removed 3 short title/cover page(s) before body text.
- `the-great-way-of-spiritual-perfection/vi` — removed 2 detected contents page(s).
- `the-great-way-of-spiritual-perfection/zh-Hans` — removed 3 detected contents page(s).
- `the-great-way-of-spiritual-perfection/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `the-great-way-of-spiritual-perfection/zh-Hant` — Traditional source `primary__big5_book_0007_0e65c9c5a4__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.954545 (1260/1320 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `teachings-at-conferences-in-the-united-states/en` — removed 1 detected contents page(s).
- `teachings-at-conferences-in-the-united-states/vi` — removed 1 detected contents page(s).
- `teachings-at-conferences-in-the-united-states/zh-Hans` — removed 3 detected contents page(s).
- `teachings-at-conferences-in-the-united-states/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-at-conferences-in-the-united-states/zh-Hant` — Traditional source `primary__big5_book_0008_c89e46eac2__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.958510 (3396/3543 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `essentials-for-further-advancement/en` — removed 3 detected contents page(s).
- `essentials-for-further-advancement/vi` — removed 3 detected contents page(s).
- `essentials-for-further-advancement/zh-Hans` — removed 6 detected contents page(s).
- `essentials-for-further-advancement/zh-Hans` — removed 1 short title/cover page(s) before body text.
- `essentials-for-further-advancement/zh-Hant` — Traditional source `primary__big5_book_0009_d8a74e3bdf__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.951825 (2529/2657 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `teachings-at-the-first-conference-in-north-america/zh-Hans` — removed 2 detected contents page(s).
- `teachings-at-the-first-conference-in-north-america/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-first-conference-in-north-america/zh-Hant` — Traditional source `primary__big5_book_0010_6090f8a75b__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.970137 (3411/3516 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `teachings-at-the-conference-in-europe/zh-Hans` — removed 2 detected contents page(s).
- `teachings-at-the-conference-in-europe/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-conference-in-europe/zh-Hant` — removed 1 detected contents page(s).
- `teachings-at-the-conference-in-europe/zh-Hant` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-conference-of-changchun-assistants/zh-Hans` — removed 2 detected contents page(s).
- `teachings-at-the-conference-of-changchun-assistants/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-conference-of-changchun-assistants/zh-Hant` — Traditional source `primary__big5_book_0012_1bff6077b5__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.963043 (3101/3220 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `teachings-at-the-conference-in-singapore/zh-Hans` — removed 2 detected contents page(s).
- `teachings-at-the-conference-in-singapore/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-conference-in-singapore/zh-Hant` — Traditional source `primary__big5_book_0013_b8d4d09e56__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.966771 (2793/2889 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `teachings-at-the-conference-in-switzerland/zh-Hans` — removed 2 detected contents page(s).
- `teachings-at-the-conference-in-switzerland/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-conference-in-switzerland/zh-Hant` — Traditional source `primary__big5_book_0014_9de2f0aaaf__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.968606 (3795/3918 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `hong-yin/en` — `/Users/GaryT/Documents/books/falun-dafa-pdf-archive/EN/Hong Yin/Alternate Translation__en_book_0015_dfd131e35f__g01.pdf`: page tree missing pages 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 80, 81; readable pages were retained.
- `hong-yin/en` — removed 2 detected contents page(s).
- `hong-yin/en` — removed 1 short title/cover page(s) before body text.
- `hong-yin/vi` — removed 1 detected contents page(s).
- `hong-yin/vi` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-conference-in-the-western-u-s/zh-Hans` — removed 2 detected contents page(s).
- `teachings-at-the-conference-in-the-western-u-s/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-conference-in-the-western-u-s/zh-Hant` — Traditional source `primary__big5_book_0016_1a7c762879__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.971663 (3669/3776 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `teachings-at-the-conference-in-the-eastern-u-s/zh-Hans` — removed 2 detected contents page(s).
- `teachings-at-the-conference-in-the-eastern-u-s/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-conference-in-the-eastern-u-s/zh-Hant` — Traditional source `primary__big5_book_0017_3a9f5b6106__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.963925 (3153/3271 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `teachings-at-the-conference-in-australia/zh-Hans` — removed 2 detected contents page(s).
- `teachings-at-the-conference-in-australia/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-conference-in-australia/zh-Hant` — Traditional source `primary__big5_book_0018_351a40969c__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.962602 (3758/3904 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `teachings-at-the-conference-in-new-zealand/zh-Hans` — removed 2 detected contents page(s).
- `teachings-at-the-conference-in-new-zealand/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-conference-in-new-zealand/zh-Hant` — removed 1 detected contents page(s).
- `teachings-at-the-conference-in-new-zealand/zh-Hant` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-conference-in-canada/zh-Hans` — removed 1 detected contents page(s).
- `teachings-at-the-conference-in-canada/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-conference-in-canada/zh-Hant` — Traditional source `primary__big5_book_0020_251534bb6f__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.979336 (3128/3194 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `teachings-at-the-midwestern-u-s-conference/zh-Hans` — removed 2 detected contents page(s).
- `teachings-at-the-midwestern-u-s-conference/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-midwestern-u-s-conference/zh-Hant` — Traditional source `primary__big5_book_0021_d477556b9b__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.947032 (2074/2190 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `guiding-the-voyage/en` — removed 1 detected contents page(s).
- `guiding-the-voyage/vi` — removed 1 detected contents page(s).
- `guiding-the-voyage/vi` — removed 1 short title/cover page(s) before body text.
- `guiding-the-voyage/zh-Hans` — removed 8 detected contents page(s).
- `guiding-the-voyage/zh-Hans` — removed 3 short title/cover page(s) before body text.
- `guiding-the-voyage/zh-Hant` — Traditional source `primary__big5_book_0022_e567441d83__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.945496 (1648/1743 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `the-essentials-of-diligent-progress-ii/en` — removed 1 detected contents page(s).
- `the-essentials-of-diligent-progress-ii/vi` — removed 3 detected contents page(s).
- `the-essentials-of-diligent-progress-ii/vi` — removed 1 short title/cover page(s) before body text.
- `the-essentials-of-diligent-progress-ii/zh-Hans` — removed 3 detected contents page(s).
- `the-essentials-of-diligent-progress-ii/zh-Hans` — removed 3 short title/cover page(s) before body text.
- `the-essentials-of-diligent-progress-ii/zh-Hant` — Traditional source `primary__big5_book_0023_e6ed358262__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.919366 (1334/1451 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `teachings-from-a-tour-of-north-america/zh-Hans` — removed 2 detected contents page(s).
- `teachings-from-a-tour-of-north-america/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-from-a-tour-of-north-america/zh-Hant` — Traditional source `primary__big5_book_0024_7097cedd9f__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.930622 (1945/2090 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `teachings-given-on-lantern-festival-day-2003/zh-Hans` — removed 2 detected contents page(s).
- `teachings-given-on-lantern-festival-day-2003/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-given-on-lantern-festival-day-2003/zh-Hant` — Traditional source `primary__big5_book_0025_d64382e596__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.951988 (4382/4603 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `hong-yin-ii/en` — `/Users/GaryT/Documents/books/falun-dafa-pdf-archive/EN/Hong Yin II/Alternate Translation__en_book_0026_259058f936__g01.pdf`: page tree missing pages 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89; readable pages were retained.
- `hong-yin-ii/en` — removed 3 detected contents page(s).
- `hong-yin-ii/zh-Hant` — removed 4 detected contents page(s).
- `hong-yin-ii/zh-Hant` — removed 1 short title/cover page(s) before body text.
- `hong-yin-ii/vi` — removed 1 detected contents page(s).
- `hong-yin-ii/vi` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-conference-in-houston/zh-Hans` — removed 2 detected contents page(s).
- `teachings-at-the-conference-in-houston/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-conference-in-houston/zh-Hant` — removed 1 detected contents page(s).
- `teachings-at-the-conference-in-houston/zh-Hant` — removed 2 short title/cover page(s) before body text.
- `collected-teachings-given-around-the-world-volume-i/en` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-i/vi` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-i/zh-Hans` — removed 3 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-i/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `collected-teachings-given-around-the-world-volume-i/zh-Hant` — removed 2 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-i/zh-Hant` — removed 2 short title/cover page(s) before body text.
- `collected-teachings-given-around-the-world-volume-ii/en` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-ii/vi` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-ii/zh-Hans` — removed 4 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-ii/zh-Hans` — removed 3 short title/cover page(s) before body text.
- `collected-teachings-given-around-the-world-volume-ii/zh-Hant` — Traditional source `primary__big5_book_0029_9e1a3f36ca__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.905967 (2900/3201 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `collected-teachings-given-around-the-world-volume-iii/en` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-iii/vi` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-iii/zh-Hans` — removed 3 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-iii/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `collected-teachings-given-around-the-world-volume-iii/zh-Hant` — Traditional source `primary__big5_book_0030_c4343d71a6__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.933194 (3129/3353 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `teaching-the-fa-at-the-discussion-on-writing-music-and-creating-fine-art/en` — removed 1 detected contents page(s).
- `teaching-the-fa-at-the-discussion-on-writing-music-and-creating-fine-art/vi` — removed 1 detected contents page(s).
- `teaching-the-fa-at-the-discussion-on-writing-music-and-creating-fine-art/zh-Hans` — removed 3 detected contents page(s).
- `teaching-the-fa-at-the-discussion-on-writing-music-and-creating-fine-art/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teaching-the-fa-at-the-discussion-on-writing-music-and-creating-fine-art/zh-Hant` — Traditional source `primary__big5_book_0031_e00101a453__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.928543 (2300/2477 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `collected-teachings-given-around-the-world-volume-iv/en` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-iv/vi` — removed 2 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-iv/zh-Hans` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-iv/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `collected-teachings-given-around-the-world-volume-iv/zh-Hant` — Traditional source `primary__big5_book_0032_b506778133__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.925870 (3060/3305 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `collected-teachings-given-around-the-world-volume-v/en` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-v/vi` — removed 2 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-v/zh-Hans` — removed 3 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-v/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `collected-teachings-given-around-the-world-volume-v/zh-Hant` — Traditional source `primary__big5_book_0033_b6475e3038__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.929524 (2717/2923 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `collected-teachings-given-around-the-world-volume-vi/en` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-vi/vi` — removed 2 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-vi/zh-Hans` — removed 3 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-vi/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `collected-teachings-given-around-the-world-volume-vi/zh-Hant` — Traditional source `primary__big5_book_0034_85790011f6__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.920736 (2602/2826 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `teachings-at-the-2004-international-conference-in-new-york/zh-Hans` — removed 2 detected contents page(s).
- `teachings-at-the-2004-international-conference-in-new-york/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-2004-international-conference-in-new-york/zh-Hant` — Traditional source `primary__big5_book_0035_218c8a230c__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.963840 (3705/3844 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `collected-teachings-given-around-the-world-volume-vii/en` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-vii/vi` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-vii/zh-Hans` — removed 3 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-vii/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `collected-teachings-given-around-the-world-volume-vii/zh-Hant` — Traditional source `primary__big5_book_0036_d22839ddd5__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.966503 (3347/3463 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `teachings-at-the-2005-conference-in-san-francisco/zh-Hans` — removed 2 detected contents page(s).
- `teachings-at-the-2005-conference-in-san-francisco/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-2005-conference-in-san-francisco/zh-Hant` — Traditional source `primary__big5_book_0037_8ef252fc2b__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.955878 (2903/3037 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `teachings-at-the-conference-in-los-angeles/zh-Hans` — removed 2 detected contents page(s).
- `teachings-at-the-conference-in-los-angeles/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `teachings-at-the-conference-in-los-angeles/zh-Hant` — removed 1 detected contents page(s).
- `teachings-at-the-conference-in-los-angeles/zh-Hant` — removed 2 short title/cover page(s) before body text.
- `hong-yin-iii/en` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `hong-yin-iii/zh-Hans` — removed 1 detected contents page(s).
- `hong-yin-iii/zh-Hans` — removed 5 short title/cover page(s) before body text.
- `hong-yin-iii/zh-Hans` — mixed Latin/CJK scripts in the extracted body; inspect before treating it as monolingual.
- `hong-yin-iii/zh-Hant` — removed 10 detected contents page(s).
- `hong-yin-iii/zh-Hant` — removed 2 short title/cover page(s) before body text.
- `hong-yin-iii/vi` — removed 1 detected contents page(s).
- `hong-yin-iii/vi` — removed 3 short title/cover page(s) before body text.
- `the-essentials-of-diligent-progress-iii/en` — removed 1 detected contents page(s).
- `the-essentials-of-diligent-progress-iii/vi` — removed 3 detected contents page(s).
- `the-essentials-of-diligent-progress-iii/zh-Hans` — removed 7 detected contents page(s).
- `the-essentials-of-diligent-progress-iii/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `the-essentials-of-diligent-progress-iii/zh-Hant` — Traditional source `primary__big5_book_0040_8fcf6941a1__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.818851 (1668/2037 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `collected-teachings-given-around-the-world-volume-viii/en` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-viii/vi` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-viii/zh-Hans` — removed 3 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-viii/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `collected-teachings-given-around-the-world-volume-viii/zh-Hant` — removed 2 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-viii/zh-Hant` — removed 2 short title/cover page(s) before body text.
- `collected-teachings-given-around-the-world-volume-ix/en` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-ix/vi` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-ix/zh-Hans` — removed 5 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-ix/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `collected-teachings-given-around-the-world-volume-ix/zh-Hant` — removed 2 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-ix/zh-Hant` — removed 2 short title/cover page(s) before body text.
- `collected-teachings-given-around-the-world-volume-x/en` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-x/vi` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-x/zh-Hans` — removed 5 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-x/zh-Hans` — removed 3 short title/cover page(s) before body text.
- `collected-teachings-given-around-the-world-volume-x/zh-Hant` — removed 2 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-x/zh-Hant` — removed 2 short title/cover page(s) before body text.
- `collected-teachings-given-around-the-world-volume-xi/en` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-xi/vi` — removed 1 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-xi/zh-Hans` — removed 6 detected contents page(s).
- `collected-teachings-given-around-the-world-volume-xi/zh-Hans` — removed 2 short title/cover page(s) before body text.
- `collected-teachings-given-around-the-world-volume-xi/zh-Hant` — Traditional source `primary__big5_book_0044_d9101e1a92__g01.pdf` was rejected and derived from Simplified: Traditional PDF failed with outside_share=0.990035 (4868/4917 CJK characters), above the 10% threshold. Derive from this group's accepted Simplified edition.
- `hong-yin-iv/en` — removed 1 short title/cover page(s) before body text.
- `hong-yin-iv/vi` — removed 1 detected contents page(s).
- `hong-yin-iv/vi` — removed 2 short title/cover page(s) before body text.
- `hong-yin-iv/zh-Hant` — removed 6 detected contents page(s).
- `hong-yin-iv/zh-Hant` — removed 2 short title/cover page(s) before body text.
- `hong-yin-v/en` — removed 1 short title/cover page(s) before body text.
- `hong-yin-v/vi` — removed 1 detected contents page(s).
- `hong-yin-v/vi` — removed 1 short title/cover page(s) before body text.
- `hong-yin-v/zh-Hant` — removed 6 detected contents page(s).
- `hong-yin-v/zh-Hant` — removed 2 short title/cover page(s) before body text.
- `hong-yin-v/zh-Hant` — replacement/private-use glyphs found in extracted text.
- `collected-fa-teachings-vol-xii/en` — removed 1 detected contents page(s).
- `collected-fa-teachings-vol-xii/zh-Hans` — removed 2 detected contents page(s).
- `collected-fa-teachings-vol-xii/zh-Hans` — removed 3 short title/cover page(s) before body text.
- `collected-fa-teachings-vol-xii/zh-Hant` — removed 2 detected contents page(s).
- `collected-fa-teachings-vol-xii/zh-Hant` — removed 2 short title/cover page(s) before body text.
- `collected-fa-teachings-vol-xiii/en` — removed 1 detected contents page(s).
- `collected-fa-teachings-vol-xiii/zh-Hans` — removed 2 detected contents page(s).
- `collected-fa-teachings-vol-xiii/zh-Hans` — removed 4 short title/cover page(s) before body text.
- `collected-fa-teachings-vol-xiii/zh-Hant` — removed 2 detected contents page(s).
- `collected-fa-teachings-vol-xiii/zh-Hant` — removed 2 short title/cover page(s) before body text.
- `collected-fa-teachings-vol-xiv/en` — removed 1 detected contents page(s).
- `collected-fa-teachings-vol-xiv/zh-Hans` — removed 2 detected contents page(s).
- `collected-fa-teachings-vol-xiv/zh-Hans` — removed 4 short title/cover page(s) before body text.
- `collected-fa-teachings-vol-xiv/zh-Hant` — removed 3 detected contents page(s).
- `collected-fa-teachings-vol-xiv/zh-Hant` — removed 2 short title/cover page(s) before body text.
- `collected-fa-teachings-vol-xv/en` — removed 1 detected contents page(s).
- `collected-fa-teachings-vol-xv/zh-Hans` — removed 3 detected contents page(s).
- `collected-fa-teachings-vol-xv/zh-Hans` — removed 3 short title/cover page(s) before body text.
- `collected-fa-teachings-vol-xv/zh-Hant` — removed 2 detected contents page(s).
- `collected-fa-teachings-vol-xv/zh-Hant` — removed 2 short title/cover page(s) before body text.
- `hong-yin-vi/en` — removed 1 short title/cover page(s) before body text.
- `hong-yin-vi/vi` — removed 1 detected contents page(s).
- `hong-yin-vi/vi` — removed 1 short title/cover page(s) before body text.
- `hong-yin-vi/zh-Hans` — removed 5 detected contents page(s).
- `hong-yin-vi/zh-Hans` — removed 3 short title/cover page(s) before body text.
- `hong-yin-vi/zh-Hant` — removed 4 detected contents page(s).
- `hong-yin-vi/zh-Hant` — removed 4 short title/cover page(s) before body text.
- `to-the-dafa-disciples-attending-the-conference-in-taiwan/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `greetings-to-the-european-fa-conference/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `to-the-czecho-slovak-fa-conference/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `to-the-2021-dafa-conference-in-taiwan/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `wake-up/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `a-strong-and-urgent-warning/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `to-the-fa-conference-in-germany/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `greetings-to-the-taiwan-fa-conference/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `on-the-general-election/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `another-stern-warning/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `stay-rational/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `congratulatory-letter/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `dafa-disciples-are-fulfilling-their-missions/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `greetings-to-the-south-america-fa-conference/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `greetings-to-the-dafa-disciples-attending-the-fa-conference-of-europe/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `to-the-fa-conference-in-france/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `to-the-canada-fa-conference/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `to-the-practitioners-of-vietnam/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `to-the-experience-sharing-conference-in-taiwan/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `to-the-2018-asia-fa-conference/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `to-the-fa-conference-of-europe/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `on-falun-dafas-classification-in-the-ordinary-world/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `a-congratulatory-letter-to-the-european-fa-conference-in-paris/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `to-the-fa-conference-in-japan/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `creating-anew/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `a-congratulatory-letter-to-the-fa-conference-of-argentina/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `a-congratulatory-letter-to-the-fa-conference-of-taiwan/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `a-greeting-to-the-south-america-fa-conference/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `on-the-responses-to-the-piece-about-assistant-souls/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `a-reminder/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `tian-guo-marching-band/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `on-dafa/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `still-so-arrogant-and-reckless/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `the-red-demon-is-incinerated-while-adamantine-ones-are-tempered/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `righteous-thoughts/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `congratulations-to-the-taiwan-fa-conference/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `stay-clearheaded/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `to-choose/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `giang-phap-tai-phap-hoi-new-york-2019/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `phap-hoi-tan-duong-nhan-va-dai-ky-nguyen-nam-2018/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `giang-phap-tai-washington-dc-nam-2018/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `giang-phap-tai-phap-hoi-new-york-ky-niem-25-nam-dai-phap-hong-truyen/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `giang-phap-tai-phap-hoi-new-york-2016/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `giang-phap-tai-phap-hoi-mien-tay-my-quoc-2015/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `giang-phap-tai-phap-hoi-new-york-2015/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `giang-phap-tai-phap-hoi-san-francisco-2014/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `giang-phap-ngay-phap-luan-dai-phap-the-gioi/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `giang-phap-o-phap-hoi-quoc-te-mien-tay-my-quoc-nam-2013/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `giang-phap-o-phap-hoi-tai-vung-do-thi-new-york-nam-2013/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `giang-phap-tai-phap-hoi-quoc-te-o-thu-do-my-quoc-2012/vi` — one-page web shell contains title, translation/link notices, and navigation but no article body; title-only content was not indexed.
- `hong-yin/vi` — manual source-text review: the extracted text layer interleaves Vietnamese transliteration with pinyin and Chinese lines; keep this flagged as mixed-language source text.
- `hong-yin-iv/zh-Hant` — manual source-text review: the source PDF's short title/cover pages contain garbled text-layer symbols; those cover pages were removed, and the extracted poem text passed the Chinese text check.
