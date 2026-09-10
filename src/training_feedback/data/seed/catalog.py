"""首发动作目录与逐动作指导草稿。

动作名称和范围以 docs/initial-exercises-and-plan.md 为权威来源。这里的内容是
应用自带的本地草稿，不代表外部专家复核或用户批准。
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ...domain.exercises import validate_guidance

BUNDLED_CONTENT_VERSION = 1

_SECONDARY_AREAS = {
    "臀桥": ("大腿后侧", "核心"),
    "蚌式开合": ("髋部", "核心"),
    "椅子深蹲": ("核心",),
    "死虫式": ("髋部",),
    "蝴蝶臀桥": ("大腿内侧", "核心"),
    "跪姿臀冲": ("大腿前侧",),
    "静态臀桥": ("大腿后侧",),
    "仰卧360°膈肌呼吸": ("胸廓",),
    "小幅猫牛式": ("核心", "颈部"),
    "坐姿90/90髋转换": ("臀部", "大腿内侧"),
    "蝴蝶式": ("髋部",),
    "仰卧4字臀部拉伸": ("髋部",),
    "半跪髋屈肌拉伸": ("大腿前侧", "核心"),
    "站立体前屈": ("臀部", "背部"),
}


def _guidance(
    *,
    purpose: str,
    starting_position: str,
    steps: tuple[str, ...],
    breathing: str,
    tempo_or_pacing: str,
    intended_sensations: tuple[str, ...],
    common_compensations: tuple[str, ...],
    stop_criteria: tuple[str, ...],
    regressions: tuple[str, ...],
    progressions: tuple[str, ...],
    equipment: tuple[str, ...],
    applicability: str,
    cautions: str,
) -> dict[str, Any]:
    return {
        "purpose": purpose,
        "starting_position": starting_position,
        "steps": [
            {"order": order, "text": text} for order, text in enumerate(steps, 1)
        ],
        "breathing": breathing,
        "tempo_or_pacing": tempo_or_pacing,
        "intended_sensations": list(intended_sensations),
        "common_compensations": list(common_compensations),
        "stop_criteria": list(stop_criteria),
        "regressions": list(regressions),
        "progressions": list(progressions),
        "equipment": list(equipment),
        "applicability": applicability,
        "cautions": cautions,
        "images": [
            {"path": None, "caption": "暂无动作示意图", "status": "missing"}
        ],
        "review": {
            "status": "draft",
            "reviewer_type": None,
            "review_source": None,
            "review_note": "",
            "reviewed_at": None,
            "user_approved_at": None,
        },
    }


def _bundle(
    exercise_key: str,
    canonical_name: str,
    category: str,
    equipment_summary: str,
    primary_areas: tuple[str, ...],
    aliases: tuple[str, ...],
    guidance: dict[str, Any],
) -> dict[str, Any]:
    content = deepcopy(guidance)
    content["primary_body_areas"] = list(primary_areas)
    content["secondary_body_areas"] = list(_SECONDARY_AREAS[canonical_name])
    return {
        "exercise_key": exercise_key,
        "canonical_name": canonical_name,
        "category": category,
        "equipment_summary": equipment_summary,
        "primary_areas": list(primary_areas),
        "secondary_areas": list(_SECONDARY_AREAS[canonical_name]),
        "body_areas": [
            *((area, True) for area in primary_areas),
            *((area, False) for area in _SECONDARY_AREAS[canonical_name]),
        ],
        "aliases": list(aliases),
        "content_id": f"training-feedback.{exercise_key}.zh-CN",
        "content_version": BUNDLED_CONTENT_VERSION,
        "guidance": content,
    }


_BUNDLED_CATALOG = (
    _bundle(
        "launch.glute-bridge",
        "臀桥",
        "main",
        "",
        ("臀部",),
        ("常规臀桥",),
        _guidance(
            purpose="强化臀部髋伸力量，并练习抬髋时保持骨盆和躯干稳定。",
            starting_position=(
                "仰卧，屈膝，双脚平放并与髋同宽；脚跟位于膝盖前下方，"
                "双臂放松置于身体两侧。"
            ),
            steps=(
                "轻收下腹，让肋骨与骨盆保持稳定，双脚均匀压地。",
                "收紧臀部并抬起髋部，直到肩、髋和膝大致连成一条斜线。",
                "在顶部保持骨盆水平，不把腰部继续向上拱。",
                "有控制地逐节放低髋部，回到起始姿势。",
            ),
            breathing="准备时吸气；抬髋时缓慢呼气，回落时吸气，全程不屏息。",
            tempo_or_pacing="平稳抬起，顶部短暂停顿，再用相近时间缓慢放下。",
            intended_sensations=("臀部明显用力", "腹部轻度参与以稳定骨盆"),
            common_compensations=(
                "用腰椎过度后仰来追求高度",
                "膝盖向内夹或向外散开",
                "只用脚尖蹬地或耸肩、颈部紧张",
            ),
            stop_criteria=(
                "腰、髋或膝出现尖锐、夹挤或持续加重的疼痛",
                "腿后侧抽筋且调整脚位后仍不能缓解",
                "无法维持呼吸或骨盆控制",
            ),
            regressions=("只做轻微骨盆后倾，不离地", "减小抬髋幅度"),
            progressions=(
                "在顶部延长短暂停留但保持自然呼吸",
                "经复核后再考虑弹力带或单腿变式",
            ),
            equipment=("瑜伽垫（可选）",),
            applicability="适合练习基础髋伸和臀部发力控制的人。",
            cautions="近期腰、髋或膝损伤者先咨询合格专业人员；动作草稿不替代医疗建议。",
        ),
    ),
    _bundle(
        "launch.clamshell",
        "蚌式开合",
        "main",
        "",
        ("臀部",),
        (),
        _guidance(
            purpose="强化髋外展与外旋控制，练习在腿部移动时稳定骨盆。",
            starting_position=(
                "侧卧，头部有支撑，髋和膝舒适屈曲，双脚跟并拢；"
                "肩、髋尽量上下叠放。"
            ),
            steps=(
                "轻收下腹，保持腰背自然，避免身体向后滚。",
                "双脚跟保持接触，缓慢抬起上侧膝盖。",
                "在骨盆仍稳定的最大舒适幅度短暂停留。",
                "缓慢合拢膝盖；完成一侧后再换边。",
            ),
            breathing="抬膝时呼气，合拢时吸气，保持连续呼吸。",
            tempo_or_pacing="小幅、慢速；抬起与放下都保持控制，不甩腿。",
            intended_sensations=("上侧臀部外侧用力", "躯干保持稳定"),
            common_compensations=(
                "骨盆和上半身一起向后翻",
                "脚跟分开或用脚甩动带起膝盖",
                "追求过大幅度导致腰侧挤压",
            ),
            stop_criteria=(
                "髋前侧、腹股沟或腰部出现夹挤或锐痛",
                "无法避免躯干滚动或屏息",
            ),
            regressions=("减小抬膝幅度", "背靠墙练习以获得骨盆位置反馈"),
            progressions=("增加顶部短暂停留", "经复核后在膝上方加轻阻力带"),
            equipment=("头部支撑物（可选）", "瑜伽垫（可选）"),
            applicability="适合需要练习臀部外侧发力和骨盆稳定的人。",
            cautions="髋关节或腹股沟正在疼痛时不要强行打开膝盖，必要时寻求专业评估。",
        ),
    ),
    _bundle(
        "launch.chair-squat",
        "椅子深蹲",
        "main",
        "chair",
        ("大腿前侧", "臀部"),
        (),
        _guidance(
            purpose="练习坐下与站起的下肢力量、髋膝协同和可控落座。",
            starting_position=(
                "把稳固、无滚轮的椅子靠墙放置；站在椅前，双脚约与髋同宽，"
                "脚掌完全着地。"
            ),
            steps=(
                "目视前方，髋部向后移动，同时屈膝向椅面下降。",
                "让膝盖朝脚尖方向，保持脚跟和前脚掌都压地。",
                "臀部轻触椅面或在可控高度停住，不向后跌坐。",
                "身体略向前，双脚发力站起，站直但不把膝盖向后顶。",
            ),
            breathing="下蹲时吸气，站起时呼气；不要用屏息来完成困难重复。",
            tempo_or_pacing="缓慢下降、轻触即起；上下过程都不借反弹。",
            intended_sensations=("大腿前侧和臀部用力", "足底均匀承重"),
            common_compensations=(
                "膝盖向内塌",
                "脚跟抬起或重心全部移到脚尖",
                "失控跌坐、用手猛推或躯干过度前扑",
            ),
            stop_criteria=(
                "膝、髋或腰出现锐痛、卡住或明显不稳",
                "头晕、胸闷或无法控制落座",
            ),
            regressions=("使用更高的稳固椅面", "双手轻扶椅扶手或固定支撑"),
            progressions=("逐渐减少手部辅助", "经复核后降低椅面或增加外部负重"),
            equipment=("稳固且无滚轮的椅子",),
            applicability="适合练习日常坐站能力和基础蹲起模式的人。",
            cautions="先确认椅子不会滑动；有跌倒风险、急性膝髋疼痛或近期手术者需专业指导。",
        ),
    ),
    _bundle(
        "launch.dead-bug",
        "死虫式",
        "main",
        "mat",
        ("核心",),
        (),
        _guidance(
            purpose="强化躯干稳定，让四肢移动时腰背仍保持可控位置。",
            starting_position=(
                "仰卧于垫上，髋膝弯曲；先抬起双臂指向上方，再在可控前提下"
                "让髋膝接近直角。"
            ),
            steps=(
                "轻收下腹，保持腰背在无疼痛且可持续的稳定位置。",
                "缓慢把一侧手臂向头后伸，同时把对侧腿向前下方伸出。",
                "只伸到腰背不拱起、骨盆不转动的幅度。",
                "回到起始位，换另一侧重复。",
            ),
            breathing="四肢伸出时慢慢呼气，回到中间时吸气；腹部用力时仍能呼吸。",
            tempo_or_pacing="每次伸出和收回都缓慢完成，中间可短暂停顿检查腰背位置。",
            intended_sensations=("腹部环绕式用力", "髋肩移动而躯干保持稳定"),
            common_compensations=(
                "腿伸得过低导致腰部拱起",
                "骨盆左右摇动",
                "耸肩、憋气或用动作速度掩盖失控",
            ),
            stop_criteria=(
                "腰部出现疼痛或明显离开可控位置",
                "髋前侧夹挤、颈部不适或无法正常呼吸",
            ),
            regressions=("双脚留在地面，只交替移动手臂", "只做脚跟轻点地面"),
            progressions=("逐渐延长手脚伸出的距离", "经复核后增加停顿或轻阻力"),
            equipment=("瑜伽垫",),
            applicability="适合练习基础核心控制且能舒适仰卧的人。",
            cautions="腰背或髋部症状、孕期或无法仰卧者应先获取个体化专业建议。",
        ),
    ),
    _bundle(
        "launch.butterfly-glute-bridge",
        "蝴蝶臀桥",
        "main",
        "",
        ("臀部",),
        (),
        _guidance(
            purpose="在髋部外旋位练习臀部髋伸，作为常规臀桥的动作变式。",
            starting_position=(
                "仰卧，屈膝，双脚脚掌相对并轻贴，膝盖向两侧自然打开；"
                "双臂放在身体两侧。"
            ),
            steps=(
                "让膝盖停在无腹股沟拉扯的自然位置，不主动向下压。",
                "轻收下腹并收紧臀部，脚外侧和脚掌相互提供稳定支撑。",
                "以小到中等幅度抬起髋部，腰背保持不过度后仰。",
                "顶部短暂停留，再缓慢放下髋部。",
            ),
            breathing="抬髋时呼气，放下时吸气，避免在顶部憋气。",
            tempo_or_pacing="用较小幅度慢速往返；以臀部控制为先，不追求高度。",
            intended_sensations=("臀部集中用力", "腹部轻度稳定"),
            common_compensations=(
                "强压膝盖向地面造成腹股沟牵拉",
                "用腰部过度后仰抬高髋部",
                "脚掌失去接触或动作过快",
            ),
            stop_criteria=(
                "腹股沟、髋前侧或膝内侧出现疼痛",
                "腰部压迫感或腿后侧持续抽筋",
            ),
            regressions=("改做常规臀桥", "减小膝盖打开角度和抬髋幅度"),
            progressions=("延长顶部短暂停留", "外部阻力仅在专业复核后使用"),
            equipment=("瑜伽垫（可选）",),
            applicability="适合作为已能稳定完成常规臀桥者的髋外旋位变式。",
            cautions="此变式对髋部舒适度要求较高；髋、腹股沟或膝有症状时不要强做。",
        ),
    ),
    _bundle(
        "launch.kneeling-hip-thrust",
        "跪姿臀冲",
        "main",
        "mat",
        ("臀部", "核心"),
        (),
        _guidance(
            purpose="在高跪姿中练习髋部屈伸和臀部发力，同时保持躯干稳定。",
            starting_position=(
                "在垫上高跪，双膝约与髋同宽，小腿和脚背舒适着地；"
                "躯干直立，必要时在身旁放稳固支撑。"
            ),
            steps=(
                "轻收下腹，保持头、胸廓和骨盆在一条稳定线上。",
                "髋部向后移动，臀部朝脚跟方向下降，躯干随髋整体移动。",
                "在膝盖舒适、腰背稳定的范围停住。",
                "收紧臀部并把髋部向前伸展，回到高跪直立位。",
            ),
            breathing="向后下降时吸气，臀部发力回到高跪时呼气。",
            tempo_or_pacing="缓慢向后、平稳向前；顶端只回到直立，不猛推髋。",
            intended_sensations=("臀部发力", "核心维持直立", "大腿前侧轻度参与"),
            common_compensations=(
                "回到顶端时腰部后仰",
                "躯干先俯下而不是从髋部移动",
                "膝盖承受压痛或左右重心不均",
            ),
            stop_criteria=(
                "膝盖压痛无法通过加垫缓解",
                "腰、髋或腹股沟出现锐痛",
                "无法保持平衡或自然呼吸",
            ),
            regressions=("增加膝下软垫并减小后移幅度", "扶稳固支撑完成动作"),
            progressions=("延长直立位臀部收紧的短暂停留", "经复核后增加轻阻力"),
            equipment=("瑜伽垫或膝下软垫",),
            applicability="适合膝部可舒适承重、需要练习跪姿髋伸控制的人。",
            cautions="膝部不能跪压、近期膝髋手术或平衡困难者应改用其他动作并咨询专业人员。",
        ),
    ),
    _bundle(
        "launch.static-glute-bridge",
        "静态臀桥",
        "main",
        "",
        ("臀部", "核心"),
        (),
        _guidance(
            purpose="以等长保持强化臀部和躯干耐力，练习稳定维持桥式位置。",
            starting_position=(
                "仰卧屈膝，双脚平放并与髋同宽，双臂置于身体两侧；"
                "先确认常规臀桥能无痛完成。"
            ),
            steps=(
                "双脚均匀压地，轻收下腹并收紧臀部。",
                "抬髋到肩、髋、膝大致连线且腰部不过度后仰的位置。",
                "按已确认计划保持，持续检查骨盆水平和呼吸。",
                "一旦姿势开始丢失就缓慢放下，不突然松力。",
            ),
            breathing="保持期间用连续、平稳的呼吸节奏，不屏息计时。",
            tempo_or_pacing="平稳进入和退出；保持时质量优先，时长以已确认计划为准。",
            intended_sensations=("臀部持续用力", "腹部持续但可呼吸的张力"),
            common_compensations=(
                "保持越久腰部越拱",
                "髋部一侧下沉或膝盖位置漂移",
                "憋气、耸肩或颈部紧张",
            ),
            stop_criteria=(
                "腰、髋或膝疼痛",
                "骨盆明显下沉且无法调整",
                "呼吸被迫中断、头晕或腿后侧抽筋",
            ),
            regressions=("降低髋部高度", "缩短保持并在每次之间完全放松"),
            progressions=("逐步延长高质量保持", "经复核后采用抬脚或外部阻力变式"),
            equipment=("瑜伽垫（可选）",),
            applicability="适合已掌握常规臀桥并需要练习等长耐力的人。",
            cautions="保持时长不是越久越好；姿势或呼吸失控时立即结束该次保持。",
        ),
    ),
    _bundle(
        "launch.supine-360-diaphragmatic-breathing",
        "仰卧360°膈肌呼吸",
        "supporting",
        "mat",
        ("核心",),
        (),
        _guidance(
            purpose="练习低负荷膈肌呼吸，感受腹部、侧腰和后腰随呼吸扩张与回落。",
            starting_position=(
                "仰卧，屈膝并让双脚平放；头颈和肩部放松。可将双手放在"
                "下肋与腹部两侧作为触觉提示。"
            ),
            steps=(
                "先自然呼气，让下颌、肩膀和腹部减少不必要紧张。",
                "从鼻腔缓慢吸气，感受下肋向两侧、腹部和后腰轻柔扩张。",
                "胸口可自然移动，但不要刻意耸肩或把腹部用力顶起。",
                "缓慢呼气，感受肋骨和腹部自然回落，再进入下一次呼吸。",
            ),
            breathing="吸气和呼气都保持安静、舒适；不需要屏息或追求最大吸气量。",
            tempo_or_pacing="以不头晕、不憋气的缓慢节奏循环，次数按已确认计划执行。",
            intended_sensations=("下肋和腹部多方向轻柔扩张", "颈肩逐渐放松"),
            common_compensations=(
                "吸气时耸肩或只抬上胸",
                "用力鼓腹、过度吸气或屏息",
                "为了压平腰部而持续用力",
            ),
            stop_criteria=("头晕、胸痛、明显气短或恐慌感", "任何新出现或加重的呼吸不适"),
            regressions=("恢复自然呼吸并缩短练习", "改为有靠背的舒适坐姿"),
            progressions=("在坐姿或四点跪姿保持同样的轻柔呼吸", "延长舒适呼气但不憋气"),
            equipment=("瑜伽垫", "头部或膝下薄垫（可选）"),
            applicability="适合作为训练准备或放松时的呼吸觉察练习。",
            cautions="这不是呼吸疾病治疗；胸痛、持续气短或已知心肺问题应先咨询医疗专业人员。",
        ),
    ),
    _bundle(
        "launch.small-cat-cow",
        "小幅猫牛式",
        "supporting",
        "mat",
        ("背部",),
        (),
        _guidance(
            purpose="以小幅度活动脊柱和骨盆，练习呼吸与躯干运动协调。",
            starting_position=(
                "四点跪姿，双手在肩下、双膝在髋下，手指展开；"
                "颈部延续脊柱方向，膝下垫面舒适。"
            ),
            steps=(
                "呼气时从骨盆开始轻轻卷动，背部小幅向上拱，头部自然跟随。",
                "在无压迫感的位置短暂停留，不用手臂猛推。",
                "吸气时骨盆向相反方向轻转，胸口略向前，腹部小幅下沉。",
                "只在舒适范围往返，保持肩膀远离耳朵。",
            ),
            breathing="呼气配合拱背，吸气配合小幅展开；如不舒适可恢复自然呼吸。",
            tempo_or_pacing="每个方向缓慢移动，不弹震、不追求最大活动范围。",
            intended_sensations=("脊柱和骨盆温和活动", "背部肌肉轻柔伸展与放松"),
            common_compensations=(
                "把动作全部挤在颈部或腰部",
                "手肘锁死、耸肩或快速甩动",
                "为追求幅度而出现疼痛",
            ),
            stop_criteria=("腕、膝、颈或腰出现锐痛或麻木放射感", "头晕或无法承受四点跪姿"),
            regressions=("进一步减小幅度", "改做有靠背坐姿的骨盆前后轻摆"),
            progressions=("在每个舒适端点增加一次自然呼吸", "逐步增加均匀的全脊柱活动"),
            equipment=("瑜伽垫", "膝下软垫（可选）"),
            applicability="适合作为训练前的低强度脊柱活动练习。",
            cautions="近期脊柱、腕或膝损伤者需要个体化调整；不要在疼痛范围反复活动。",
        ),
    ),
    _bundle(
        "launch.seated-90-90-hip-switch",
        "坐姿90/90髋转换",
        "supporting",
        "",
        ("髋部",),
        (),
        _guidance(
            purpose="练习髋关节内外旋活动和坐姿骨盆控制。",
            starting_position=(
                "坐在地面，两膝弯曲、双脚分开；双手可放在身后支撑，"
                "先让双膝向一侧落到舒适的近似90/90位置。"
            ),
            steps=(
                "坐骨尽量均匀承重，胸口自然抬起，不强压膝盖贴地。",
                "双膝缓慢回到中间，再一起转向另一侧。",
                "脚掌可随转换调整，但动作主要来自髋部旋转。",
                "在每侧舒适位置短暂停留，然后继续交替。",
            ),
            breathing="转换过程中保持自然呼吸，到达每侧时缓慢呼气。",
            tempo_or_pacing="慢速连续转换；不用惯性甩膝，也不在端点弹压。",
            intended_sensations=("髋部深层温和活动", "臀部和大腿内外侧轻度拉伸"),
            common_compensations=(
                "用手猛推地面带动双腿",
                "骨盆完全离地或身体大幅后仰",
                "强压膝盖造成髋前侧夹挤",
            ),
            stop_criteria=("髋前侧、腹股沟或膝内侧出现夹挤和锐痛", "麻木、卡住或无法控制转换"),
            regressions=("双手在身后提供更多支撑", "减小双膝下降幅度或只练单侧静态位置"),
            progressions=("逐渐减少手部支撑", "在保持躯干稳定时增加舒适转换幅度"),
            equipment=("瑜伽垫或坐垫（可选）",),
            applicability="适合需要温和练习髋旋转活动且能安全坐地的人。",
            cautions="髋撞击、术后限制或膝部疼痛者不要强求90度角度，应先获取专业建议。",
        ),
    ),
    _bundle(
        "launch.butterfly-stretch",
        "蝴蝶式",
        "supporting",
        "",
        ("大腿内侧",),
        (),
        _guidance(
            purpose="温和拉伸大腿内侧和髋部内收肌群，作为训练后的放松动作。",
            starting_position=(
                "坐在地面或坐垫上，屈膝并让双脚脚掌相对；双手轻扶脚踝或小腿，"
                "脊柱自然延伸。"
            ),
            steps=(
                "把双脚放在髋部舒适距离，不强行拉近。",
                "让膝盖依靠重力向两侧自然下降，不用手向下压。",
                "如需增加感受，从髋部轻微前倾并保持背部不过度弓起。",
                "按已确认计划保持后，缓慢合拢双膝退出。",
            ),
            breathing="保持时缓慢、自然呼吸，每次呼气仅放松紧张，不强压幅度。",
            tempo_or_pacing="缓慢进入和退出，静态保持时不弹震；时长以已确认计划为准。",
            intended_sensations=("大腿内侧和腹股沟附近温和牵拉",),
            common_compensations=(
                "用手或肘用力把膝盖压向地面",
                "含胸弓腰追求前倾距离",
                "在疼痛端点弹震",
            ),
            stop_criteria=("腹股沟、髋或膝出现锐痛、夹挤或麻木", "牵拉感持续增强而不能放松"),
            regressions=("把双脚移远并在膝下放支撑", "坐在较高坐垫上保持躯干直立"),
            progressions=("在背部稳定时从髋部略微前倾", "逐步延长舒适保持而不施加外力"),
            equipment=("坐垫或膝下支撑（可选）",),
            applicability="适合作为内侧大腿和髋部的温和放松练习。",
            cautions="髋或膝有急性症状、孕期或术后活动限制者应先咨询专业人员。",
        ),
    ),
    _bundle(
        "launch.supine-figure-four-stretch",
        "仰卧4字臀部拉伸",
        "supporting",
        "mat",
        ("臀部",),
        (),
        _guidance(
            purpose="温和拉伸臀部和髋后侧，并用仰卧姿势减少平衡要求。",
            starting_position=(
                "仰卧屈膝，双脚平放；将一侧脚踝轻放到另一侧大腿上，"
                "避开直接压在膝盖骨上。"
            ),
            steps=(
                "保持头、肩和骨盆放松贴稳，交叉侧脚踝轻轻回勾。",
                "若已有足够牵拉就保持；需要时双手抱住支撑腿大腿后侧。",
                "把支撑腿缓慢带向胸前，直到臀部出现温和牵拉。",
                "按已确认计划保持后缓慢放回，解除交叉并换侧。",
            ),
            breathing="保持时自然呼吸，呼气时放松臀部，不用呼吸去强迫幅度。",
            tempo_or_pacing="缓慢进入、静态保持、缓慢退出；不拉扯或弹震。",
            intended_sensations=("交叉侧臀部和髋后侧温和牵拉",),
            common_compensations=(
                "用手直接压交叉侧膝盖",
                "头肩抬起或骨盆明显扭转",
                "拉得过近造成髋前侧夹挤",
            ),
            stop_criteria=("膝、髋或腹股沟锐痛", "腿部麻木、刺痛或症状向下放射"),
            regressions=("支撑脚留在地面，不把腿拉向胸前", "在交叉膝下放软垫支撑"),
            progressions=("在保持骨盆稳定时轻微拉近支撑腿", "逐步延长舒适保持"),
            equipment=("瑜伽垫",),
            applicability="适合作为臀部和髋后侧的低平衡需求拉伸。",
            cautions="坐骨神经样症状、髋膝损伤或术后限制者应停止自行加深并寻求专业建议。",
        ),
    ),
    _bundle(
        "launch.half-kneeling-hip-flexor-stretch",
        "半跪髋屈肌拉伸",
        "supporting",
        "mat",
        ("髋前侧",),
        (),
        _guidance(
            purpose="温和拉伸后侧跪姿腿的髋前侧，同时练习骨盆和躯干对齐。",
            starting_position=(
                "一膝跪在软垫上，另一脚踩在前方形成半跪姿；前脚完全着地，"
                "身旁可放稳固支撑。"
            ),
            steps=(
                "躯干保持直立，轻收下腹，让骨盆不过度前倾。",
                "身体作为整体缓慢向前移动，前膝朝脚尖方向。",
                "在后侧髋前方出现温和牵拉时停住，不用腰部后仰增加幅度。",
                "按已确认计划保持，缓慢退回并换侧。",
            ),
            breathing="保持时连续自然呼吸，呼气时维持骨盆位置并放松不必要紧张。",
            tempo_or_pacing="缓慢进入和退出，静态保持不弹震；时长以已确认计划为准。",
            intended_sensations=("后侧跪姿腿的髋前方和大腿上部温和牵拉",),
            common_compensations=(
                "通过腰部后仰代替髋部向前移动",
                "前膝向内塌或身体左右倾斜",
                "跪姿膝盖直接压在硬地面",
            ),
            stop_criteria=("跪姿膝、髋前侧或腰部出现锐痛", "麻木、明显不稳或无法正常呼吸"),
            regressions=("扶稳固支撑并减小前移幅度", "增加膝下软垫或改用站姿变式"),
            progressions=("保持骨盆稳定时略增前移幅度", "逐步延长舒适保持"),
            equipment=("瑜伽垫或膝下软垫", "稳固支撑（可选）"),
            applicability="适合膝部可承受半跪、需要放松髋前侧的人。",
            cautions="膝部不能跪压、髋部术后或平衡困难者应改用专业人员建议的替代动作。",
        ),
    ),
    _bundle(
        "launch.standing-forward-fold",
        "站立体前屈",
        "supporting",
        "",
        ("大腿后侧",),
        (),
        _guidance(
            purpose="以站姿温和放松大腿后侧和背部，并练习从髋部折叠。",
            starting_position=(
                "双脚约与髋同宽站立，膝盖保持微屈，体重均匀落在双脚；"
                "身前可放稳固椅子或桌面支撑。"
            ),
            steps=(
                "先拉长脊柱，髋部向后移动并从髋部开始前倾。",
                "双手放在大腿、椅面或其他稳固支撑上，不强求触地。",
                "在腿后侧出现温和牵拉的位置保持，膝盖可继续微屈。",
                "退出时屈膝并收紧臀腿，缓慢回到直立；站稳后再抬头。",
            ),
            breathing="保持时自然呼吸，不屏息；回到站立后先稳定呼吸再移动。",
            tempo_or_pacing="缓慢下移与回起，不弹震、不快速甩头；保持时长按已确认计划。",
            intended_sensations=("大腿后侧和臀部下缘温和牵拉", "背部舒适延展"),
            common_compensations=(
                "锁死膝盖并强拉到最大幅度",
                "从腰部塌折、耸肩或为了触地弹震",
                "快速起身导致头晕或失去平衡",
            ),
            stop_criteria=("头晕、视物异常或失去平衡", "腰腿锐痛、麻木或放射症状"),
            regressions=("双手扶高处并减小前倾", "改做坐姿单腿后侧拉伸"),
            progressions=("在背部稳定时逐步降低手部支撑", "逐步延长舒适保持而不锁膝"),
            equipment=("稳固椅子或桌面（可选）",),
            applicability="适合能安全站立、需要温和放松后侧链的人。",
            cautions="易头晕、平衡困难、急性腰腿症状或医生限制头低位者不应独立完成。",
        ),
    ),
)


def bundled_catalog() -> list[dict[str, Any]]:
    """Return an isolated copy so callers cannot mutate bundled source content."""
    return deepcopy(list(_BUNDLED_CATALOG))


# 保留既有公开目录形状，避免范围清单在调用方重复维护。
CATALOG = [
    (
        item["canonical_name"],
        item["category"],
        item["equipment_summary"],
        list(item["primary_areas"]),
        list(item["aliases"]),
    )
    for item in _BUNDLED_CATALOG
]


def seed_catalog(connection) -> None:
    from ..exercise_repositories import ExerciseRepository

    # 启动只负责初始化全新的空目录；已有目录的内容更新必须由显式流程完成。
    if connection.execute("SELECT 1 FROM exercise LIMIT 1").fetchone() is not None:
        return
    repository = ExerciseRepository(connection)
    with connection:
        for item in bundled_catalog():
            validation = validate_guidance(
                item["guidance"], require_body_areas=True
            )
            if not validation.complete:
                raise ValueError(
                    f"Bundled guidance is incomplete: {item['canonical_name']}"
                )
            exercise_id = repository.create(
                item["canonical_name"],
                item["category"],
                item["equipment_summary"],
                item["body_areas"],
                bundled_exercise_key=item["exercise_key"],
            )
            for alias in item["aliases"]:
                repository.add_alias(exercise_id, alias)
            repository.add_guidance_revision(
                exercise_id,
                item["guidance"],
                bundled_content_id=item["content_id"],
                bundled_content_version=item["content_version"],
            )
        connection.commit()
