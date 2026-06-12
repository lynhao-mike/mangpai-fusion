# Rule Type Audit

审计范围：

- theory/ziping/index.yaml
- theory/tiaohou_ditiansui/index.yaml

审计性质：只读规则类型分类审计。本文只为每条规则分配建议 rule_type，不修改规则文件、权重或 Schema。

分类口径：

- GENERAL_PRINCIPLE：理论总纲、通用原则、上游解释框架。
- STRUCTURE：结构性规则、格局类规则、十神组合、用神成败、从化、合冲、清浊、通关等。
- EVENT：特定生活事项或事件落点，如婚姻、六亲、子息、健康、事业、财富、功名、性情等。
- TIMING：应期、流年、大运、岁运触发、动态转化规则。
- EXPLANATION：仅作说明、注释、背景解释，不直接参与判断的规则。
- ANTI_PATTERN：禁用孤证、反机械套用、异常/反例/不可直接推断类规则。

> 注：本次分类是治理审计建议，不等同于写入规则 Schema；如未来落地，应经过人工复核。

## 1. 每条规则的 rule_id + rule_type

| Source | Rule ID | Rule Type | Title | Topic |
|---|---|---|---|---|
| ziping | ZP-PROD-20260605-001 | EVENT | 用神为全局关键 | yongshen |
| ziping | ZP-PROD-20260605-002 | ANTI_PATTERN | 财格要看身财关系 | wealth_structure |
| ziping | ZP-PROD-20260605-003 | STRUCTURE | 用神以月令为第一出处 | yongshen_month_branch |
| ziping | ZP-PROD-20260605-004 | STRUCTURE | 身旺身弱决定取用方向 | shenqiang_shenruo |
| ziping | ZP-PROD-20260605-005 | STRUCTURE | 用神成败决定全局吉凶 | yongshen_success_failure |
| ziping | ZP-PROD-20260605-006 | ANTI_PATTERN | 用神受克要看救应 | jiuying |
| ziping | ZP-PROD-20260605-007 | EVENT | 格局纯杂影响高低 | geju_chunza |
| ziping | ZP-PROD-20260605-008 | STRUCTURE | 用神有情无情决定格局高低 | yongshen_youqing |
| ziping | ZP-PROD-20260605-009 | STRUCTURE | 调候为急，先救气候再论扶抑 | tiaohou_priority |
| ziping | ZP-PROD-20260605-010 | STRUCTURE | 相神受伤往往比局部受伤更伤格 | xiangshen |
| ziping | ZP-PROD-20260605-011 | STRUCTURE | 四吉神失宜也可能破格 | sijishen |
| ziping | ZP-PROD-20260605-012 | STRUCTURE | 四凶神制化得宜可成贵格 | sixiongshen_zhihua |
| ziping | ZP-PROD-20260605-013 | STRUCTURE | 正官格以清纯为贵 | zhengguan_ge |
| ziping | ZP-PROD-20260605-014 | STRUCTURE | 从化从势专旺属于特殊取用逻辑 | special_geju |
| ziping | ZP-PROD-20260605-015 | STRUCTURE | 格局高低应与有情、纯杂、护卫联合判断 | geju_level_composite |
| ziping | ZP-PROD-20260605-016 | TIMING | 成败可随运岁转化 | timing_transformation |
| ziping | ZP-PROD-20260605-017 | ANTI_PATTERN | 财官多寡也要取用，不可只看数量 | wealth_official_quantity |
| ziping | ZP-PROD-20260605-018 | STRUCTURE | 格例总纲适合作为规则索引入口 | geju_index |
| ziping | ZP-PROD-20260606-001 | STRUCTURE | 五行生克与支干源流先定骨架 | wuxing_ganzhi_framework |
| ziping | ZP-PROD-20260606-002 | STRUCTURE | 月令与提纲决定先后次序 | yueling_tigang |
| ziping | ZP-PROD-20260606-003 | STRUCTURE | 合冲刑害改变气机通塞 | he_chong_xing_hai |
| ziping | ZP-PROD-20260606-004 | STRUCTURE | 财官印食伤须随身强身弱取用 | shishen_by_strength |
| ziping | ZP-PROD-20260606-005 | EVENT | 通月气有倚托则贵 | tong_yueqi_yituo |
| ziping | ZP-PROD-20260606-006 | EVENT | 禄归时与时柱能改晚景 | lugui_shizhu |
| ziping | ZP-PROD-20260606-007 | STRUCTURE | 财库官库印库需钥匙冲开 | ku_key_open |
| ziping | ZP-PROD-20260606-008 | EVENT | 时柱日时断法重晚景子息与收官 | rishi_shizhu |
| ziping | ZP-PROD-20260606-009 | ANTI_PATTERN | 伤官见官与伤官伤尽必须分辨 | shangguan_official |
| ziping | ZP-PROD-20260606-010 | EVENT | 特殊格局要先辨真伪再谈贵气 | special_geju_authenticity |
| ziping | ZP-PROD-20260606-011 | TIMING | 行运能放大或逆转原局成败 | yunshi_geju_change |
| ziping | ZP-PROD-20260606-012 | EVENT | 刑冲破害常落在六亲与子息 | xingchong_liuqin_zixi |
| ziping | ZP-PROD-20260606-013 | STRUCTURE | 五行过不及贵在中道 | wuxing_zhongdao |
| ziping | ZP-PROD-20260606-014 | EVENT | 五行皆赖土以成载化 | wuxing_laitu_zaihua |
| ziping | ZP-PROD-20260606-015 | GENERAL_PRINCIPLE | 木赖水生但多水漂流 | mu_shuisheng_piaoliu |
| ziping | ZP-PROD-20260606-016 | GENERAL_PRINCIPLE | 春木火暖水滋为美 | chunmu_huoshui_xiangji |
| ziping | ZP-PROD-20260606-017 | EVENT | 甲木寒木向阳主富贵 | jiamu_hanmu_xiangyang |
| ziping | ZP-PROD-20260606-018 | EVENT | 水泛木浮需戊己制水 | shuifan_mufu_wuji |
| ziping | ZP-PROD-20260606-019 | STRUCTURE | 夏木根燥需水润而忌火旺 | xiamu_shuirun_jihuowang |
| ziping | ZP-PROD-20260606-020 | GENERAL_PRINCIPLE | 秋甲先丁后庚以成材 | qiujiamu_dinggeng_chengcai |
| ziping | ZP-PROD-20260606-021 | GENERAL_PRINCIPLE | 冬甲丁先庚后丙佐 | dongjiamu_dinggeng_bingzuo |
| ziping | ZP-PROD-20260606-022 | GENERAL_PRINCIPLE | 乙木丙癸不可离 | yimu_binggui |
| ziping | ZP-PROD-20260606-023 | GENERAL_PRINCIPLE | 丙火多以壬水辅映成既济 | binghuo_renshui_jiji |
| ziping | ZP-PROD-20260606-024 | GENERAL_PRINCIPLE | 丁火须甲引庚劈 | dinghuo_jiayin_gengpi |
| ziping | ZP-PROD-20260606-025 | STRUCTURE | 土聚滞散轻须水木调和 | tuju_tuzhi_shuimu |
| ziping | ZP-PROD-20260606-026 | GENERAL_PRINCIPLE | 戊土丙甲癸三者为关键调配 | wutu_bingjiagui |
| ziping | ZP-PROD-20260606-027 | GENERAL_PRINCIPLE | 夏己取癸为要次用丙火 | xiaji_gui_bing |
| ziping | ZP-PROD-20260606-028 | GENERAL_PRINCIPLE | 秋己癸先丙后以润暖收藏 | qiuji_gui_bing |
| ziping | ZP-PROD-20260606-029 | GENERAL_PRINCIPLE | 冬己丙暖为尊见火不孤见土不贫 | dongji_binghuo |
| ziping | ZP-PROD-20260606-030 | GENERAL_PRINCIPLE | 金无火炼不能成器但火力须平衡 | jinhuo_chengqi |
| ziping | ZP-PROD-20260606-031 | GENERAL_PRINCIPLE | 金局水火土偏失则沉枯埋没 | jinju_shuihuotu |
| ziping | ZP-PROD-20260606-032 | GENERAL_PRINCIPLE | 金已成器不欲再火 | jin_chengqi_zaihuo |
| ziping | ZP-PROD-20260606-033 | GENERAL_PRINCIPLE | 春金喜火荣身厚土辅助忌水盛增寒 | chunjin_huotu |
| ziping | ZP-PROD-20260606-034 | STRUCTURE | 庚金按月令取用先辨丙丁甲壬 | gengjin_yueling_quyong |
| ziping | ZP-PROD-20260606-035 | GENERAL_PRINCIPLE | 庚金戌亥丑月防土埋寒冻须甲壬丙丁 | gengjin_maihan |
| ziping | ZP-PROD-20260606-036 | GENERAL_PRINCIPLE | 辛金畏土叠喜壬淘洗兼用己壬 | xinjin_jiren |
| ziping | ZP-PROD-20260606-037 | GENERAL_PRINCIPLE | 水不绝源赖金生泛滥赖土防 | shuiju_jinyuan_tudi |
| ziping | ZP-PROD-20260606-038 | ANTI_PATTERN | 壬水汪洋须戊堤庚源丙暖随月调配 | renshui_yueling |
| ziping | ZP-PROD-20260606-039 | GENERAL_PRINCIPLE | 癸水柔弱喜辛源丙暖冬须解冻 | guishui_xinbing |
| tiaohou_ditiansui | DTS-PROD-20260605-001 | EVENT | 命贵中和，偏枯有损 | zhonghe_pianku |
| tiaohou_ditiansui | DTS-PROD-20260605-002 | GENERAL_PRINCIPLE | 地支冲需视强弱喜忌 | chong_dong |
| tiaohou_ditiansui | DTS-PROD-20260605-003 | ANTI_PATTERN | 天地人三元一体看命 | sanyuan |
| tiaohou_ditiansui | DTS-PROD-20260605-004 | STRUCTURE | 地有刚柔、命有偏全 | pianku_pianquan |
| tiaohou_ditiansui | DTS-PROD-20260605-005 | STRUCTURE | 干支顺而不悖为吉 | shunni |
| tiaohou_ditiansui | DTS-PROD-20260605-006 | STRUCTURE | 理会衰旺进退，判断五行状态 | wangshuai_jintui |
| tiaohou_ditiansui | DTS-PROD-20260605-007 | ANTI_PATTERN | 用神不拘名美名恶 | yongshen_functional |
| tiaohou_ditiansui | DTS-PROD-20260605-008 | STRUCTURE | 扶抑要看去留舒配 | fuyi_quliu |
| tiaohou_ditiansui | DTS-PROD-20260605-009 | STRUCTURE | 天干地支的顺接与层次感 | ganzhi_flow |
| tiaohou_ditiansui | DTS-PROD-20260605-010 | TIMING | 阳刚阴柔因时而显 | yinyang_shiling |
| tiaohou_ditiansui | DTS-PROD-20260605-011 | GENERAL_PRINCIPLE | 冲动与生克要结合强弱判断 | chong_strength |
| tiaohou_ditiansui | DTS-PROD-20260605-012 | GENERAL_PRINCIPLE | 得令者冲衰则拔，失时者冲旺无伤 | chong_de令_strength |
| tiaohou_ditiansui | DTS-PROD-20260605-013 | STRUCTURE | 中和平正优先于奇异结构 | zhonghe_vs_qiyi |
| tiaohou_ditiansui | DTS-PROD-20260605-014 | STRUCTURE | 用神可跨类别，不以十神名义先入为主 | yongshen_cross_category |
| tiaohou_ditiansui | DTS-PROD-20260605-015 | STRUCTURE | 以四季定五行旺衰 | season_strength |
| tiaohou_ditiansui | DTS-PROD-20260605-016 | STRUCTURE | 吉凶取决于顺逆而非单纯强弱 | shunni_vs_strength |
| tiaohou_ditiansui | DTS-PROD-20260605-017 | STRUCTURE | 进退可解释五行阶段变化 | jintui_dynamic |
| tiaohou_ditiansui | DTS-PROD-20260605-018 | GENERAL_PRINCIPLE | 现实判断要回到能否应事 | falsifiable_application |
| tiaohou_ditiansui | DTS-PROD-20260605-019 | GENERAL_PRINCIPLE | 地支冲需区分去凶与激凶 | chong_quji_jiji |
| tiaohou_ditiansui | DTS-PROD-20260606-001 | EVENT | 寒暖先定命局生机 | han暖_shengji |
| tiaohou_ditiansui | DTS-PROD-20260606-002 | STRUCTURE | 燥湿失中则难成 | zaoshi_balance |
| tiaohou_ditiansui | DTS-PROD-20260606-003 | ANTI_PATTERN | 吉神宜显凶神宜藏但需看根气 | yinxian_jixiong |
| tiaohou_ditiansui | DTS-PROD-20260606-004 | STRUCTURE | 众寡之势决定去向 | zhonggua_shili |
| tiaohou_ditiansui | DTS-PROD-20260606-005 | STRUCTURE | 震兑之理随季而变 | zhendui_seasonal_strategy |
| tiaohou_ditiansui | DTS-PROD-20260606-006 | STRUCTURE | 坎离之中重升降和解制 | kanli_shengjiang |
| tiaohou_ditiansui | DTS-PROD-20260606-007 | STRUCTURE | 何知章适合做快速诊断索引 | hezhi_index |
| tiaohou_ditiansui | DTS-PROD-20260606-008 | EVENT | 元神厚者寿气浊神枯者夭 | yuanshen_shouyao |
| tiaohou_ditiansui | DTS-PROD-20260606-009 | EVENT | 女命先看夫星与格局清浊 | female_fuxing_qingzhuo |
| tiaohou_ditiansui | DTS-PROD-20260606-010 | STRUCTURE | 小儿命宜和平而气势攸长 | child_qishi_yangcheng |
| tiaohou_ditiansui | DTS-PROD-20260606-011 | EVENT | 从象要分从旺从强从气从势 | congxiang_types |
| tiaohou_ditiansui | DTS-PROD-20260606-012 | STRUCTURE | 真化必须看化神与衰旺 | huaxiang_huashen |
| tiaohou_ditiansui | DTS-PROD-20260606-013 | STRUCTURE | 假从亦可发但须假行真运 | jiacong_zhenyun |
| tiaohou_ditiansui | DTS-PROD-20260606-014 | STRUCTURE | 假从按从财从官分别取真运 | jiacong_fencai_fenguan |
| tiaohou_ditiansui | DTS-PROD-20260606-015 | TIMING | 假从岁运不悖可源浊流清 | jiacong_yuanzhuoliuqing |
| tiaohou_ditiansui | DTS-PROD-20260606-016 | STRUCTURE | 假化比真化尤难须辨杂象 | jiahua_zaxiang |
| tiaohou_ditiansui | DTS-PROD-20260606-017 | TIMING | 假化可借岁运抑假扶真 | jiahua_suiyun_fuzhen |
| tiaohou_ditiansui | DTS-PROD-20260606-018 | GENERAL_PRINCIPLE | 顺局以食伤生财秀气流行为贵 | shunju_shishang_shengcai |
| tiaohou_ditiansui | DTS-PROD-20260606-019 | STRUCTURE | 顺局最忌印运次忌官运 | shunju_ji_yinguan |
| tiaohou_ditiansui | DTS-PROD-20260606-020 | STRUCTURE | 反局之君赖臣生以财破旺印 | fanju_junlai_chensheng |
| tiaohou_ditiansui | DTS-PROD-20260606-021 | GENERAL_PRINCIPLE | 儿能救母须分时候 | erneng_jiumu_shihou |
| tiaohou_ditiansui | DTS-PROD-20260606-022 | EVENT | 母慈灭子宜顺母性忌逆犯 | muci_miezi |
| tiaohou_ditiansui | DTS-PROD-20260606-023 | STRUCTURE | 三元以干支藏干分天地人 | sanyuan_ganzhi_canggan |
| tiaohou_ditiansui | DTS-PROD-20260606-024 | STRUCTURE | 天干地支顺而不悖为贵 | shunbei_ganzhi |
| tiaohou_ditiansui | DTS-PROD-20260606-025 | STRUCTURE | 命贵中和平正奇异不足凭 | zhonghe_pingzheng |
| tiaohou_ditiansui | DTS-PROD-20260606-026 | STRUCTURE | 子平全在四柱五行用神不可滥取神煞奇格 | wuzhi_yongshen_fanshensha |
| tiaohou_ditiansui | DTS-PROD-20260606-027 | ANTI_PATTERN | 用神不拘名目当扶抑则扶抑 | yongshen_buju_mingmu |
| tiaohou_ditiansui | DTS-PROD-20260606-028 | STRUCTURE | 旺相休囚重在进退之机 | wangxiang_xiuqiu_jintui |
| tiaohou_ditiansui | DTS-PROD-20260606-029 | STRUCTURE | 十干体象不可机械类比 | shigan_fan_jixieleixiang |
| tiaohou_ditiansui | DTS-PROD-20260606-030 | STRUCTURE | 甲木火炽乘龙水宕骑虎以地支救偏 | jiamu_chenglong_qihu |
| tiaohou_ditiansui | DTS-PROD-20260606-031 | STRUCTURE | 丙火泄威用己遏焰用壬顺性用辛 | binghuo_jirenxin |
| tiaohou_ditiansui | DTS-PROD-20260606-032 | STRUCTURE | 地支冲动须看生方库败与强弱喜忌 | dizhi_chongdong_fenlei |
| tiaohou_ditiansui | DTS-PROD-20260606-033 | STRUCTURE | 刑害破多穿凿总以生克为凭 | xinghai_po_shengke |
| tiaohou_ditiansui | DTS-PROD-20260606-034 | GENERAL_PRINCIPLE | 暗冲暗会按喜忌彼我判断 | anchong_anhui_biwo |
| tiaohou_ditiansui | DTS-PROD-20260606-035 | STRUCTURE | 旺冲衰则拔衰冲旺则发 | wangshuai_chong |
| tiaohou_ditiansui | DTS-PROD-20260606-036 | STRUCTURE | 天覆地载方成上下有情 | tianfu_dizai |
| tiaohou_ditiansui | DTS-PROD-20260606-037 | STRUCTURE | 始终得所须干支流通一无弃物 | shizhong_desuo |
| tiaohou_ditiansui | DTS-PROD-20260606-038 | GENERAL_PRINCIPLE | 两气成象不可破局取运贵一路澄清 | liangqi_chengxiang |
| tiaohou_ditiansui | DTS-PROD-20260606-039 | GENERAL_PRINCIPLE | 生局必须食为美印局秀气不足 | shengju_shiqi |
| tiaohou_ditiansui | DTS-PROD-20260606-040 | ANTI_PATTERN | 五气成形须互济不可过缺 | wuqi_chengxing |
| tiaohou_ditiansui | DTS-PROD-20260606-041 | TIMING | 成形得用岁运可补成 | sui_yun_bucheng |
| tiaohou_ditiansui | DTS-PROD-20260606-042 | STRUCTURE | 独象喜行化地化神要昌 | duxiang_huashen |
| tiaohou_ditiansui | DTS-PROD-20260606-043 | STRUCTURE | 独象怕破局合象喜制化成功 | duxiang_hexuang |
| tiaohou_ditiansui | DTS-PROD-20260606-044 | GENERAL_PRINCIPLE | 全象喜财须观局中意向 | quanxiang_cai |
| tiaohou_ditiansui | DTS-PROD-20260606-045 | STRUCTURE | 旺弱组合决定喜财喜官喜印 | xishen_zuhe |
| tiaohou_ditiansui | DTS-PROD-20260606-046 | STRUCTURE | 形全宜损形缺宜补 | xingquan_xingque |
| tiaohou_ditiansui | DTS-PROD-20260606-047 | STRUCTURE | 泄伤帮助手段须分用 | xieshang_bangzhu |
| tiaohou_ditiansui | DTS-PROD-20260606-048 | GENERAL_PRINCIPLE | 方局不必忌混但三字全方可取 | fangju_hunju |
| tiaohou_ditiansui | DTS-PROD-20260606-049 | STRUCTURE | 方局齐来须天干顺气 | fangju_tiangan |
| tiaohou_ditiansui | DTS-PROD-20260606-050 | ANTI_PATTERN | 成方透元神不宜再帮从强例外 | chengfang_congqiang |
| tiaohou_ditiansui | DTS-PROD-20260606-051 | ANTI_PATTERN | 八格取用先月令透干司令定真假 | bage_quyong |
| tiaohou_ditiansui | DTS-PROD-20260606-052 | STRUCTURE | 正变格均归五行正理 | zhengli_waige |
| tiaohou_ditiansui | DTS-PROD-20260606-053 | STRUCTURE | 格局不可执一病药随印财比劫转化 | geju_bingyao |
| tiaohou_ditiansui | DTS-PROD-20260606-054 | STRUCTURE | 体为形象气局无形局则日主为体 | tiyong_xingqi |
| tiaohou_ditiansui | DTS-PROD-20260606-055 | STRUCTURE | 旺极弱极不可逆治宜从其势 | wangji_ruoji |
| tiaohou_ditiansui | DTS-PROD-20260606-056 | STRUCTURE | 精神气分损益求中 | jingshenqi |
| tiaohou_ditiansui | DTS-PROD-20260606-057 | STRUCTURE | 月令为提纲气象格局用神皆属司令 | yueling_tigang |
| tiaohou_ditiansui | DTS-PROD-20260606-058 | EVENT | 生时归宿喜忌增减不及月令 | shizhu_guishu |
| tiaohou_ditiansui | DTS-PROD-20260606-059 | STRUCTURE | 衰旺不可按得时失令死法定 | shuaiwang_sifa |
| tiaohou_ditiansui | DTS-PROD-20260606-060 | STRUCTURE | 地支根气重于天干比肩 | genqi_bijian |
| tiaohou_ditiansui | DTS-PROD-20260606-061 | GENERAL_PRINCIPLE | 太旺太衰似异类宜顺极势 | taiwang_tairuo |
| tiaohou_ditiansui | DTS-PROD-20260606-062 | STRUCTURE | 中和为主有病有药仍不离补偏却余 | zhonghe_bingyao |
| tiaohou_ditiansui | DTS-PROD-20260606-063 | STRUCTURE | 源流以旺神为源收局阻节定休咎 | yuanliu |
| tiaohou_ditiansui | DTS-PROD-20260606-064 | TIMING | 通关为引通克制岁运可冲合间神 | tongguan |
| tiaohou_ditiansui | DTS-PROD-20260606-065 | STRUCTURE | 通关须去间神方能杀印相生 | tongguan_shayin |
| tiaohou_ditiansui | DTS-PROD-20260606-066 | STRUCTURE | 官杀可混不可混取决势从与日主旺衰 | guansha_hunza |
| tiaohou_ditiansui | DTS-PROD-20260606-067 | ANTI_PATTERN | 去官去杀以清为贵合留须辨化不化 | quguan_qusha |
| tiaohou_ditiansui | DTS-PROD-20260606-068 | STRUCTURE | 财滋弱杀须身能任且财杀互根 | cai_zi_ruosha |
| tiaohou_ditiansui | DTS-PROD-20260606-069 | STRUCTURE | 杀重用印以一仁化众杀 | shazhong_yinyin |
| tiaohou_ditiansui | DTS-PROD-20260606-070 | STRUCTURE | 食神制杀贵制化中和忌制过 | shishen_zhisha |
| tiaohou_ditiansui | DTS-PROD-20260606-071 | STRUCTURE | 合官留杀或合杀留官须以用神清浊判断 | heguan_liusha |
| tiaohou_ditiansui | DTS-PROD-20260606-072 | STRUCTURE | 官杀混杂坐印气贯反多富贵 | guansha_zuoyin |
| tiaohou_ditiansui | DTS-PROD-20260606-073 | STRUCTURE | 制杀太过不如官杀混杂有情 | zhisha_taiguo |
| tiaohou_ditiansui | DTS-PROD-20260606-074 | STRUCTURE | 伤官见官须按用财印劫伤官分格 | shangguan_jianguan |
| tiaohou_ditiansui | DTS-PROD-20260606-075 | STRUCTURE | 伤官用印忌财坏印用财忌印夺财 | shangguan_yongyin_yongcai |
| tiaohou_ditiansui | DTS-PROD-20260606-076 | EVENT | 伤官用劫用伤用官各有成败路径 | shangguan_fenxing |
| tiaohou_ditiansui | DTS-PROD-20260606-077 | EVENT | 假伤官日主旺极喜伤泄菁华 | jia_shangguan |
| tiaohou_ditiansui | DTS-PROD-20260606-078 | EVENT | 伤官用神不可损伤冲破则落职破败 | shangguan_yongshen_sun |
| tiaohou_ditiansui | DTS-PROD-20260606-079 | ANTI_PATTERN | 清气不等于一气成局须喜神有气安顿 | qingqi |
| tiaohou_ditiansui | DTS-PROD-20260606-080 | TIMING | 澄浊求清须岁运冲滞制闲扶喜 | chengzhuo_qiuqing |
| tiaohou_ditiansui | DTS-PROD-20260606-081 | EVENT | 浊气须分气格财比劫印食伤浊 | zhuoqi_fenlei |
| tiaohou_ditiansui | DTS-PROD-20260606-082 | STRUCTURE | 宁清中浊不可清中枯 | qingku |
| tiaohou_ditiansui | DTS-PROD-20260606-083 | STRUCTURE | 真神为提纲司令透干得用 | zhenshen |
| tiaohou_ditiansui | DTS-PROD-20260606-084 | TIMING | 假神得局亦可取用须审岁运扶抑 | jiashen_deju |
| tiaohou_ditiansui | DTS-PROD-20260606-085 | STRUCTURE | 真神失势假神得局可反以假作真 | jiashen_deju |
| tiaohou_ditiansui | DTS-PROD-20260606-086 | STRUCTURE | 假神为用逢运坏假亦成凶 | jiashen_deju |
| tiaohou_ditiansui | DTS-PROD-20260606-087 | EVENT | 刚柔制化须引其性情不可概定硬克 | gangrou_zhihua |
| tiaohou_ditiansui | DTS-PROD-20260606-088 | STRUCTURE | 克泄引从四法须分局势审用 | gangrou_zhihua |
| tiaohou_ditiansui | DTS-PROD-20260606-089 | STRUCTURE | 当令得势宜泄菁华失令休囚宜向虚寻实 | wangshuai_quyong |
| tiaohou_ditiansui | DTS-PROD-20260606-090 | GENERAL_PRINCIPLE | 当令得势权在一人不可逆其气势 | shunni |
| tiaohou_ditiansui | DTS-PROD-20260606-091 | GENERAL_PRINCIPLE | 二人同心宜顺势引通不可勉强制伏 | shunni |
| tiaohou_ditiansui | DTS-PROD-20260606-092 | GENERAL_PRINCIPLE | 逆来顺去为富基顺来逆去为贫意 | shunni |
| tiaohou_ditiansui | DTS-PROD-20260606-093 | STRUCTURE | 寒暖须有气有根不可过偏 | han暖_tiaohou |
| tiaohou_ditiansui | DTS-PROD-20260606-094 | ANTI_PATTERN | 寒暖无根无气反不宜强用 | han暖_tiaohou |
| tiaohou_ditiansui | DTS-PROD-20260606-095 | GENERAL_PRINCIPLE | 紧冲为克遥冲为动须辨距离与力量 | dizhi_chong |
| tiaohou_ditiansui | DTS-PROD-20260606-096 | EVENT | 燥湿偏枯湿滞无成燥烈有祸 | zaoshi_tiaohou |
| tiaohou_ditiansui | DTS-PROD-20260606-097 | STRUCTURE | 夏木须水与湿土冬金须火与燥土 | zaoshi_tiaohou |
| tiaohou_ditiansui | DTS-PROD-20260606-098 | GENERAL_PRINCIPLE | 吉神太露易争夺凶物深藏成患 | yinxian |
| tiaohou_ditiansui | DTS-PROD-20260606-099 | STRUCTURE | 吉露凶藏仍须看当令通根休囚 | yinxian |
| tiaohou_ditiansui | DTS-PROD-20260606-100 | STRUCTURE | 众寡强弱须分去寡成众两路 | zhonggua |
| tiaohou_ditiansui | DTS-PROD-20260606-101 | GENERAL_PRINCIPLE | 众寡须分日主与四柱两端论 | zhonggua |
| tiaohou_ditiansui | DTS-PROD-20260606-102 | STRUCTURE | 震兑金木相成有攻成润从暖五法 | zhendui |
| tiaohou_ditiansui | DTS-PROD-20260606-103 | GENERAL_PRINCIPLE | 春初木嫩金坚宜火攻金 | zhendui |
| tiaohou_ditiansui | DTS-PROD-20260606-104 | GENERAL_PRINCIPLE | 仲春木旺金衰宜土成金木之用 | zhendui |
| tiaohou_ditiansui | DTS-PROD-20260606-105 | GENERAL_PRINCIPLE | 夏木泄金燥宜水润金木 | zhendui |
| tiaohou_ditiansui | DTS-PROD-20260606-106 | STRUCTURE | 秋木凋金锐宜土从金势 | zhendui |
| tiaohou_ditiansui | DTS-PROD-20260606-107 | GENERAL_PRINCIPLE | 冬木衰金寒宜火暖木制金 | zhendui |
| tiaohou_ditiansui | DTS-PROD-20260606-108 | STRUCTURE | 坎离水火相持有升降和解制五法 | kanli |
| tiaohou_ditiansui | DTS-PROD-20260606-109 | GENERAL_PRINCIPLE | 天干离衰地支坎旺宜木升地气 | kanli |
| tiaohou_ditiansui | DTS-PROD-20260606-110 | GENERAL_PRINCIPLE | 天干坎衰地支离旺宜金降天气 | kanli |
| tiaohou_ditiansui | DTS-PROD-20260606-111 | GENERAL_PRINCIPLE | 天干皆火地支皆水须木运和之 | kanli |
| tiaohou_ditiansui | DTS-PROD-20260606-112 | STRUCTURE | 天干皆水地支皆火须金运解之 | kanli |
| tiaohou_ditiansui | DTS-PROD-20260606-113 | TIMING | 水火交战须岁运制强扶弱 | kanli |
| tiaohou_ditiansui | DTS-PROD-20260606-114 | EVENT | 夫妻以财为妻但须按喜神清浊活看 | liuqin_fuqi |
| tiaohou_ditiansui | DTS-PROD-20260606-115 | EVENT | 克妻须分身财官杀印食伤组合不可执劫刃 | liuqin_fuqi |
| tiaohou_ditiansui | DTS-PROD-20260606-116 | EVENT | 日主喜财财合闲神化财得妻财化忌主外情 | liuqin_fuqi |
| tiaohou_ditiansui | DTS-PROD-20260606-117 | EVENT | 子女以食伤为主兼看日主旺衰喜忌通变 | liuqin_zinv |
| tiaohou_ditiansui | DTS-PROD-20260606-118 | EVENT | 身旺食伤有力无印多子印重食轻子少 | liuqin_zinv |
| tiaohou_ditiansui | DTS-PROD-20260606-119 | EVENT | 身弱食伤重或官杀重无印比子息艰难 | liuqin_zinv |
| tiaohou_ditiansui | DTS-PROD-20260606-120 | EVENT | 八字用神即子星得子多在用神运年 | liuqin_zinv |
| tiaohou_ditiansui | DTS-PROD-20260606-121 | EVENT | 父母祖业重在年月喜忌财官印绶 | liuqin_fumu |
| tiaohou_ditiansui | DTS-PROD-20260606-122 | EVENT | 年月官印相生日时不犯主荫庇儿荣 | liuqin_fumu |
| tiaohou_ditiansui | DTS-PROD-20260606-123 | EVENT | 兄弟以比劫禄刃论须看日主爱憎不只提纲 | liuqin_xiongdi |
| tiaohou_ditiansui | DTS-PROD-20260606-124 | EVENT | 劫刃太旺财官无气兄弟反拖累 | liuqin_xiongdi |
| tiaohou_ditiansui | DTS-PROD-20260606-125 | EVENT | 富看财气通门户重生化有情不在财多 | caiqi_tongmenhu |
| tiaohou_ditiansui | DTS-PROD-20260606-126 | GENERAL_PRINCIPLE | 身旺财弱无官须食伤财旺无食须官杀 | caiqi_tongmenhu |
| tiaohou_ditiansui | DTS-PROD-20260606-127 | STRUCTURE | 官星有理会以财印劫食伤调其清浊 | guanxing_lihui |
| tiaohou_ditiansui | DTS-PROD-20260606-128 | GENERAL_PRINCIPLE | 身旺官杀混杂得财印相济亦可发贵 | guansha_hunza |
| tiaohou_ditiansui | DTS-PROD-20260606-129 | STRUCTURE | 财神不真九类皆由财与喜忌流通失当 | caishen_buzhen |
| tiaohou_ditiansui | DTS-PROD-20260606-130 | STRUCTURE | 财官虽美须日主旺相能任 | cai_guan_chengzai |
| tiaohou_ditiansui | DTS-PROD-20260606-131 | STRUCTURE | 官星不见分上等下等可判贤不肖 | guanxing_bujian |
| tiaohou_ditiansui | DTS-PROD-20260606-132 | STRUCTURE | 喜神为辅弼用神有喜则吉无喜逢忌则凶 | xishen_fubi |
| tiaohou_ditiansui | DTS-PROD-20260606-133 | STRUCTURE | 忌神辗转攻须以喜神为药扶喜抑忌 | jishen_gong |
| tiaohou_ditiansui | DTS-PROD-20260606-134 | EVENT | 寿看性定元神厚五行停匀喜用不悖 | shouyuan_yuanshen |
| tiaohou_ditiansui | DTS-PROD-20260606-135 | EVENT | 元神源流厚生化有情主寿势较稳 | shouyuan_yuanshen |
| tiaohou_ditiansui | DTS-PROD-20260606-136 | ANTI_PATTERN | 寿局亦须兼看财官子息根气虚实 | shouyuan_fenlun |
| tiaohou_ditiansui | DTS-PROD-20260606-137 | EVENT | 食神有力制杀亦可福寿但性情另论 | shishen_zhisha |
| tiaohou_ditiansui | DTS-PROD-20260606-138 | TIMING | 气浊主用浅忌重行运党忌之寿险 | qizhuo_shouyao |
| tiaohou_ditiansui | DTS-PROD-20260606-139 | EVENT | 气浊短寿风险与子息不必同断 | shouxi_zixi_fenlun |
| tiaohou_ditiansui | DTS-PROD-20260606-140 | EVENT | 神枯主身弱印重身旺无泄及寒燥枯槁 | shenku_shouyao |
| tiaohou_ditiansui | DTS-PROD-20260606-141 | EVENT | 女命先观夫星盛衰再察格局清浊 | nvming_fuxing_geju |
| tiaohou_ditiansui | DTS-PROD-20260606-142 | STRUCTURE | 女命三奇二德咸池驿马不可机械定贵贱贞淫 | nvming_fanshensha |
| tiaohou_ditiansui | DTS-PROD-20260606-143 | EVENT | 女命夫星即用神子星即喜神须通变 | nvming_fuzi_tongbian |
| tiaohou_ditiansui | DTS-PROD-20260606-144 | EVENT | 女命身旺无官而财得令得局亦可成上格 | nvming_caiyong |
| tiaohou_ditiansui | DTS-PROD-20260606-145 | EVENT | 官旺身弱可取印为夫以护身承官 | nvming_yinweifu |
| tiaohou_ditiansui | DTS-PROD-20260606-146 | EVENT | 女命克夫风险须看官财印伤比综合失衡 | nvming_banlv_yali |
| tiaohou_ditiansui | DTS-PROD-20260606-147 | EVENT | 女命子息须按身强弱与伤财印官杀生化判断 | nvming_zixi |
| tiaohou_ditiansui | DTS-PROD-20260606-148 | EVENT | 多合贪合可致婚恋关系重心偏移 | tanhe_hunlian |
| tiaohou_ditiansui | DTS-PROD-20260606-149 | EVENT | 财生官印扶身食神得地一气相生主夫荣子贵 | nvming_fuzi_shenghua |
| tiaohou_ditiansui | DTS-PROD-20260606-150 | EVENT | 女命伤官旺得合化或印制可转为清秀 | nvming_shangguan_zhihua |
| tiaohou_ditiansui | DTS-PROD-20260606-151 | EVENT | 寒木向阳官印双清财生官不坏印为佳 | hanmu_xiangyang |
| tiaohou_ditiansui | DTS-PROD-20260606-152 | STRUCTURE | 湿土能生金晦火蓄水燥土可脆金助火枯水 | zaoshi_tu |
| tiaohou_ditiansui | DTS-PROD-20260606-153 | GENERAL_PRINCIPLE | 小儿命重四柱和平气势攸长不重神煞关杀 | xiaoer_heping |
| tiaohou_ditiansui | DTS-PROD-20260606-154 | TIMING | 小儿易养须生化有情流通不悖运途安祥 | xiaoer_yiyang |
| tiaohou_ditiansui | DTS-PROD-20260606-155 | EVENT | 小儿财官太旺身弱运根拔尽则难养 | xiaoer_nanyang |
| tiaohou_ditiansui | DTS-PROD-20260606-156 | STRUCTURE | 金多水浊母多子病偏枯无火不可误作贵格 | jinshui_pianhan |
| tiaohou_ditiansui | DTS-PROD-20260606-157 | STRUCTURE | 身弱官皆杀身旺杀皆官关键看印财制化 | guansha_qiangruo |
| tiaohou_ditiansui | DTS-PROD-20260606-158 | STRUCTURE | 才德判断看格局清浊五行情势不作道德定罪 | caide_lun |
| tiaohou_ditiansui | DTS-PROD-20260606-159 | STRUCTURE | 德胜才主和平纯粹格正局清 | deshengcai |
| tiaohou_ditiansui | DTS-PROD-20260606-160 | STRUCTURE | 才胜德主偏气杂乱多争多合 | caishengde |
| tiaohou_ditiansui | DTS-PROD-20260606-161 | EVENT | 奋发之机在用喜得力忌神失势闲神不党忌 | fenfa_zhiji |
| tiaohou_ditiansui | DTS-PROD-20260606-162 | STRUCTURE | 沉埋之气在太过缺陷用失令喜弱忌旺 | chenmai_zhiqi |
| tiaohou_ditiansui | DTS-PROD-20260606-163 | STRUCTURE | 喜神远隔得合神引近为恩中有媒 | enxuan_mei |
| tiaohou_ditiansui | DTS-PROD-20260606-164 | GENERAL_PRINCIPLE | 喜神被忌隔占或合助忌神为恩中起怨 | enxuan_yuan |
| tiaohou_ditiansui | DTS-PROD-20260606-165 | STRUCTURE | 闲神不伤体用不碍喜神时不用不动 | xianshen_budong |
| tiaohou_ditiansui | DTS-PROD-20260606-166 | TIMING | 闲神要紧之场可制化岁运忌物而作自家 | xianshen_zuoyong |
| tiaohou_ditiansui | DTS-PROD-20260606-167 | STRUCTURE | 用神有余不足决定喜忌仇闲的相对身份 | xiji_dynamic |
| tiaohou_ditiansui | DTS-PROD-20260606-168 | STRUCTURE | 合宜化化喜则利化忌则咎合而不化为羁绊 | hehua_xiji |
| tiaohou_ditiansui | DTS-PROD-20260606-169 | STRUCTURE | 用喜被贪合所绊易废志失用 | tanhe_shiyong |
| tiaohou_ditiansui | DTS-PROD-20260606-170 | EVENT | 逢冲得用为冲去贪恋反成有情 | fengchong_deyong |
| tiaohou_ditiansui | DTS-PROD-20260606-171 | STRUCTURE | 真从须日主孤立无气且财官强甚 | zhencong |
| tiaohou_ditiansui | DTS-PROD-20260606-172 | STRUCTURE | 从象不止财官兼有从旺从强从气从势 | congxiang_zonggang |
| tiaohou_ditiansui | DTS-PROD-20260606-173 | STRUCTURE | 从旺为比劫极旺有印生无官杀制 | congwang |
| tiaohou_ditiansui | DTS-PROD-20260606-174 | STRUCTURE | 从强为印比重重日主当令无财官杀气 | congqiang |
| tiaohou_ditiansui | DTS-PROD-20260606-175 | STRUCTURE | 从气按木火金水气势顺行反此必凶 | congqi |
| tiaohou_ditiansui | DTS-PROD-20260606-176 | STRUCTURE | 从势为日主无根财官食伤并旺须和解 | congshi |
| tiaohou_ditiansui | DTS-PROD-20260606-177 | STRUCTURE | 从财须食伤吐秀化比劫生财 | congcai_shishang |
| tiaohou_ditiansui | DTS-PROD-20260606-178 | EVENT | 从杀真局逢冲破杀局或日主得根即破 | congsha_poge |
| tiaohou_ditiansui | DTS-PROD-20260606-179 | EVENT | 从旺从气之局可顺不可逆 | congwang_congqi_shunni |
| tiaohou_ditiansui | DTS-PROD-20260606-180 | EVENT | 从金水气势忌无根火土南方破局 | cong_jinshui_poge |
| tiaohou_ditiansui | DTS-PROD-20260606-181 | STRUCTURE | 从势从官忌帮身冲去通关财星 | congshi_congguan_tongguan |
| tiaohou_ditiansui | DTS-PROD-20260606-182 | EVENT | 从化金水忌燥土伤官助劫 | conghua_jinshui_zaotu |
| tiaohou_ditiansui | DTS-PROD-20260606-183 | ANTI_PATTERN | 真化须合神真实并得逢五逢辰化气 | zhenhua_tiaojian |
| tiaohou_ditiansui | DTS-PROD-20260606-184 | STRUCTURE | 真化既成只论化神不以本气争合妒合 | zhenhua_huashen |
| tiaohou_ditiansui | DTS-PROD-20260606-185 | STRUCTURE | 化神旺而有余宜泄化神 | huashen_youyu |
| tiaohou_ditiansui | DTS-PROD-20260606-186 | STRUCTURE | 化神衰而不足宜生助化神 | huashen_buzu |
| tiaohou_ditiansui | DTS-PROD-20260606-187 | EVENT | 合而不化多为羁绊争妒不佳 | heerbuhua_jiban |
| tiaohou_ditiansui | DTS-PROD-20260606-188 | STRUCTURE | 假从虽有暗扶但财官破印制劫亦可从势 | jiacong_tiaojian |
| tiaohou_ditiansui | DTS-PROD-20260606-189 | STRUCTURE | 假行真运亦可取富贵 | jiacong_zhenyun |
| tiaohou_ditiansui | DTS-PROD-20260606-190 | EVENT | 假从财有比劫宜官杀食伤有印宜财破印 | jiacongcai_xiyun |
| tiaohou_ditiansui | DTS-PROD-20260606-191 | EVENT | 假从官杀有比劫喜官有食伤喜财有印喜财破印 | jiacong_guansha_xiyun |
| tiaohou_ditiansui | DTS-PROD-20260606-192 | EVENT | 假从源浊流清可由微而起 | jiacong_yuanzhuoliuqing |
| tiaohou_ditiansui | DTS-PROD-20260606-193 | STRUCTURE | 假化比真化尤难须辨六类假化机 | jiahua_leixing |
| tiaohou_ditiansui | DTS-PROD-20260606-194 | TIMING | 假化须岁运扶合神制忌神方能趋真 | jiahua_zhenyun |
| tiaohou_ditiansui | DTS-PROD-20260606-195 | STRUCTURE | 从儿格以食伤成气月令为门户 | conger_menhu |
| tiaohou_ditiansui | DTS-PROD-20260606-196 | STRUCTURE | 从儿不论身强弱仍去生助食伤 | conger_bulun_shenqiangruo |
| tiaohou_ditiansui | DTS-PROD-20260606-197 | EVENT | 从儿又得儿以食伤生财为富贵流通 | conger_shishangshengcai |
| tiaohou_ditiansui | DTS-PROD-20260606-198 | EVENT | 从儿最忌印运次忌官运 | conger_jiyun |
| tiaohou_ditiansui | DTS-PROD-20260606-199 | TIMING | 从儿行运不背逢财多主富贵聪明 | conger_caixing_chengjiu |
| tiaohou_ditiansui | DTS-PROD-20260606-200 | STRUCTURE | 君赖臣生为印太旺须财止印托根 | junlai_chensheng |
| tiaohou_ditiansui | DTS-PROD-20260606-201 | STRUCTURE | 儿能救母须分时令以我生者制克我者 | erneng_jiumu |
| tiaohou_ditiansui | DTS-PROD-20260606-202 | STRUCTURE | 母慈灭子为印旺财无气不可破印须顺母助子 | muci_miezi |
| tiaohou_ditiansui | DTS-PROD-20260606-203 | EVENT | 夫健怕妻重在主体健旺否则为财多身弱 | fujian_paqi |
| tiaohou_ditiansui | DTS-PROD-20260606-204 | STRUCTURE | 战局天干战可制地支战急须合会库息争 | zhanju_tiandizhan |
| tiaohou_ditiansui | DTS-PROD-20260606-205 | STRUCTURE | 两不冲一为谬冲即克但用神伏藏反宜冲动 | chong_fayong |
| tiaohou_ditiansui | DTS-PROD-20260606-206 | STRUCTURE | 天地交战若无制化多主速凶有制化可存可发 | tiandi_jiaozhan |
| tiaohou_ditiansui | DTS-PROD-20260606-207 | STRUCTURE | 合局喜合助喜去凶动局得静 | heju_yihe |
| tiaohou_ditiansui | DTS-PROD-20260606-208 | EVENT | 合局忌合助忌羁喜掩动及化凶 | heju_buyi |
| tiaohou_ditiansui | DTS-PROD-20260606-209 | GENERAL_PRINCIPLE | 君象君盛臣衰宜泄上益下不可抗君 | junxiang |
| tiaohou_ditiansui | DTS-PROD-20260606-210 | STRUCTURE | 臣象臣盛君衰宜损下益上不可激臣 | chenxiang |
| tiaohou_ditiansui | DTS-PROD-20260606-211 | GENERAL_PRINCIPLE | 母象母众子孤宜助子势忌水金触母伤子 | muxiang |
| tiaohou_ditiansui | DTS-PROD-20260606-212 | GENERAL_PRINCIPLE | 子象子众母衰宜安母忌土金失衡 | zixiang |
| tiaohou_ditiansui | DTS-PROD-20260606-213 | EVENT | 性情以五气中和偏枯转译为行为风格 | xingqing_zhonghe_pianku |
| tiaohou_ditiansui | DTS-PROD-20260606-214 | STRUCTURE | 五气相生无争战主风格平和稳定 | xingqing_pinghe |
| tiaohou_ditiansui | DTS-PROD-20260606-215 | GENERAL_PRINCIPLE | 土虚木多金缺阴火不生湿土主合作诚信风险 | xingqing_chengxin_fengxian |
| tiaohou_ditiansui | DTS-PROD-20260606-216 | EVENT | 科名秀气重清气官星不起难登正途 | keming_qingqi_guanxing |
| tiaohou_ditiansui | DTS-PROD-20260606-217 | TIMING | 清气可发秀运途破清则困场屋 | keming_yuntu_poqing |
| tiaohou_ditiansui | DTS-PROD-20260606-218 | EVENT | 格局不显遇合宜运亦可科甲连登 | keming_yuntu_zhuxi |
| tiaohou_ditiansui | DTS-PROD-20260606-219 | EVENT | 异路功名重日干有气财官相通 | yilu_gongming_caiguan |
| tiaohou_ditiansui | DTS-PROD-20260606-220 | TIMING | 异路高卑看清纯气势与运途损益 | yilu_gongming_gaodi |
| tiaohou_ditiansui | DTS-PROD-20260606-221 | EVENT | 财官虽通日主失衡劫伤夹杂则难出身 | yilu_chengbai_chengzai |
| tiaohou_ditiansui | DTS-PROD-20260606-222 | EVENT | 高位权责须天然清气与喜神有情 | diwei_qingqi_xishen |
| tiaohou_ditiansui | DTS-PROD-20260606-223 | STRUCTURE | 刃杀神清可任强权责刃不当权难贵显 | rensha_shenqing |
| tiaohou_ditiansui | DTS-PROD-20260606-224 | STRUCTURE | 刃旺杀弱神气不清主强势对抗风险 | rensha_xingqing_fengxian |
| tiaohou_ditiansui | DTS-PROD-20260606-225 | STRUCTURE | 地方部门任事重财官清纯日元生旺 | diwei_caiguan_renzhi |
| tiaohou_ditiansui | DTS-PROD-20260606-226 | EVENT | 事业格局虽佳五行失调亦损家庭稳定 | shiye_jiating_fenyu |
| tiaohou_ditiansui | DTS-PROD-20260606-227 | STRUCTURE | 基层辅职亦看一点清气清浊定职责范围 | diwei_qingzhuo_jiceng |
| tiaohou_ditiansui | DTS-PROD-20260606-228 | STRUCTURE | 干支升降分清浊支气上升干气下降 | qingzhuo_ganzhi_shengjiang |
| tiaohou_ditiansui | DTS-PROD-20260606-229 | TIMING | 运途重地支天干不背十年不可截看 | suiyun_dayun_zhengti |
| tiaohou_ditiansui | DTS-PROD-20260606-230 | GENERAL_PRINCIPLE | 喜运干支同气或干生支为厚支生干气泄 | suiyun_xiyun_houbao |
| tiaohou_ditiansui | DTS-PROD-20260606-231 | STRUCTURE | 盖头截脚使吉凶减半或喜运难兑现 | suiyun_gaitou_jiejiao |
| tiaohou_ditiansui | DTS-PROD-20260606-232 | STRUCTURE | 太岁重天干兼究地支天克地冲最凶 | suiyun_taisui_tiankedichong |
| tiaohou_ditiansui | DTS-PROD-20260606-233 | TIMING | 岁运战冲和好按喜忌坐支力量制化定胜负 | suiyun_zhanchonghehao |
| tiaohou_ditiansui | DTS-PROD-20260606-234 | ANTI_PATTERN | 合而能化方吉合而不化反为羁绊 | hehua_jiban |
| tiaohou_ditiansui | DTS-PROD-20260606-235 | GENERAL_PRINCIPLE | 好为同类帮扶须通根有力方切 | suiyun_haotonglei_tonggen |
| tiaohou_ditiansui | DTS-PROD-20260606-236 | EVENT | 贞元看阶段循环与传承不作寿限断 | zhenyuan_jieduan_chuancheng |

## 2. 每个 rule_type 的统计数量

| Rule Type | Count | Share |
|---|---:|---:|
| GENERAL_PRINCIPLE | 55 | 17.6% |
| STRUCTURE | 147 | 47.1% |
| EVENT | 73 | 23.4% |
| TIMING | 19 | 6.1% |
| EXPLANATION | 0 | 0.0% |
| ANTI_PATTERN | 18 | 5.8% |
| TOTAL | 312 | 100.0% |

### 分库统计

| Source | Total | GENERAL_PRINCIPLE | STRUCTURE | EVENT | TIMING | EXPLANATION | ANTI_PATTERN |
|---|---:|---:|---:|---:|---:|---:|---:|
| ziping | 57 | 19 | 21 | 10 | 2 | 0 | 5 |
| tiaohou_ditiansui | 255 | 36 | 126 | 63 | 17 | 0 | 13 |

## 3. rule_type 分布不均警示

- STRUCTURE 数量为 147，占比 47.1%，为绝对主体；两库明显以结构、格局、取用、成败、组合判断为主。
- EVENT 数量为 73，占比 23.4%；事件落点规则少于结构类，未来反馈可能难以直接映射到婚姻、健康、财富、事业等域。
- TIMING 数量为 19，占比 6.1%；相对结构类明显偏少，岁运/流年/应期校准能力不足。
- ANTI_PATTERN 数量为 18，占比 5.8%；禁用孤证、反机械套用、防误判规则偏少，否决/降权防线不足。
- GENERAL_PRINCIPLE 数量为 55，占比 17.6%；理论总纲多被写成结构规则，容易和细则混投。
- EXPLANATION 数量为 0，占比 0.0%；解释层几乎没有独立成型，判断层与解释层存在混写风险。
- 滴天髓/调候规则数量显著多于子平，若未来按 rule 粒度投票，滴天髓中的 STRUCTURE 会对整体分类分布产生主导影响。

## 4. 对未来案例校准可能产生的风险说明

1. 结构类规则过多会造成结构性偏置：未来案例校准可能更容易奖励格局、用神、从化、合冲、通关等结构判断，而低估具体事件反馈。
2. 应期类规则偏少会影响时间校准：当反馈包含年份、大运、流年变化时，系统可能只能校准“原局是否像”，无法稳定校准“何时发生”。
3. EVENT 类规则相对不足会导致生活领域映射不稳：事业、财富、婚姻、健康等反馈可能被迫回流到 STRUCTURE，形成权重污染。
4. ANTI_PATTERN 偏少会放大误判：限制性规则如果不能作为显式否决/降权机制，系统会更容易机械套用、孤证定论。
5. GENERAL_PRINCIPLE 若与 STRUCTURE 同权投票，会导致理论总纲和细分规则重复加权；总纲更适合作为 gate、解释框架或 family-level cap。
6. EXPLANATION 缺位会影响报告解释层治理：解释性文字可能被误当成判断证据，造成可解释性与可校准性混淆。

## 5. 治理建议

- 将 GENERAL_PRINCIPLE 设为上游 gate 或解释依据，不与结构细则同权累加。
- 将 STRUCTURE 拆为主结构票与辅助结构证据，避免同源结构多次投票。
- 为 TIMING 建立独立校准通道，确保未来反馈能校准应期准确性。
- 将 ANTI_PATTERN 改为显式否决/降权类型，优先处理孤证、机械套用和误判防线。
- 按反馈域补齐 EVENT 规则，减少从结构判断直接跳到事件结论的风险。
- 建立 rule_type 与 rule_family 的交叉治理矩阵，避免同一 family 中 GENERAL_PRINCIPLE、STRUCTURE、EVENT、TIMING 重复投票。
