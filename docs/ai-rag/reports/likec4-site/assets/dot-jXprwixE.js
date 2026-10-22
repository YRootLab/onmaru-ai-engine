var e=e=>{switch(e){case`index`:return`digraph {
    graph [TBbalance=min,
        bgcolor=transparent,
        compound=true,
        fontname=Arial,
        fontsize=20,
        labeljust=l,
        labelloc=t,
        layout=dot,
        likec4_viewId=index,
        nodesep=1.528,
        outputorder=nodesfirst,
        pad=0.209,
        rankdir=TB,
        ranksep=1.667,
        splines=spline
    ];
    node [color="#2563eb",
        fillcolor="#3b82f6",
        fontcolor="#eff6ff",
        fontname=Arial,
        label="\\N",
        penwidth=0,
        shape=rect,
        style=filled
    ];
    edge [arrowsize=0.75,
        color="#8D8D8D",
        fontcolor="#C9C9C9",
        fontname=Arial,
        fontsize=14,
        penwidth=2,
        style=""
    ];
    traveler [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">여행자</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">OnMaru 웹에서 대화형 여정 검색을 요청하고 검증된 결과를 받는다.</FONT></TD></TR></TABLE>>,
        likec4_id=traveler,
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    onmaru [height=2.5,
        label=<<FONT POINT-SIZE="20">OnMaru</FONT>>,
        likec4_id=onmaru,
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    traveler -> onmaru [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">대화 질문 입력</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ HTTPS ]</FONT></TD></TR></TABLE>>,
        likec4_id=dtzrtb,
        minlen=1,
        style=dashed];
    admin [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">운영자</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Grafana 검토 큐에서 품질 저하 사례를 선택해 격리 실험을 시작하고 승격을<BR/>승인한다.</FONT></TD></TR></TABLE>>,
        likec4_id=admin,
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    admin -> onmaru [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14"><B>[...]</B></FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ operator initiated ]</FONT></TD></TR></TABLE>>,
        likec4_id=gqdisv,
        minlen=1,
        style=dashed];
    gemini [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Gemini API</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Google AI</FONT></TD></TR></TABLE>>,
        likec4_id=gemini,
        likec4_level=0,
        margin="0.5,0.223",
        width=4.584];
    onmaru -> gemini [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14"><B>[...]</B></FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ HTTPS · no member transcript ]</FONT></TD></TR></TABLE>>,
        likec4_id=iy6o5d,
        style=dashed];
    observability [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Grafana Cloud</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">공통 trace 조회, metric/dashboard/alerts, 품질 검토</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">OTel / Prometheus compatible</FONT></TD></TR></TABLE>>,
        likec4_id=observability,
        likec4_level=0,
        margin="0.5,0.223",
        width=4.584];
    onmaru -> observability [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14"><B>[...]</B></FONT></TD></TR></TABLE>>,
        likec4_id="1x0tul9",
        minlen=1,
        style=dashed];
    gemini -> onmaru [arrowhead=normal,
        label=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14"><B>[...]</B></FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ HTTPS ]</FONT></TD></TR></TABLE>>,
        likec4_id="1f3wnvl",
        style=dashed];
}
`;case`system-context`:return`digraph {
    graph [TBbalance=min,
        bgcolor=transparent,
        compound=true,
        fontname=Arial,
        fontsize=20,
        labeljust=l,
        labelloc=t,
        layout=dot,
        likec4_viewId="system-context",
        nodesep=0.973,
        outputorder=nodesfirst,
        pad=0.209,
        rankdir=LR,
        ranksep=1.389,
        splines=ortho
    ];
    node [color="#2563eb",
        fillcolor="#3b82f6",
        fontcolor="#eff6ff",
        fontname=Arial,
        label="\\N",
        penwidth=0,
        shape=rect,
        style=filled
    ];
    edge [arrowsize=0.75,
        color="#8D8D8D",
        fontcolor="#C9C9C9",
        fontname=Arial,
        fontsize=14,
        penwidth=2,
        style=""
    ];
    traveler [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">여행자</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">OnMaru 웹에서 대화형 여정 검색을 요청하고 검증된 결과를 받는다.</FONT></TD></TR></TABLE>>,
        likec4_id=traveler,
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    onmaru [height=2.5,
        label=<<FONT POINT-SIZE="20">OnMaru</FONT>>,
        likec4_id=onmaru,
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    traveler -> onmaru [arrowhead=normal,
        likec4_id=dtzrtb,
        minlen=1,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">대화 질문 입력</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ HTTPS ]</FONT></TD></TR></TABLE>>];
    admin [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">운영자</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Grafana 검토 큐에서 품질 저하 사례를 선택해 격리 실험을 시작하고 승격을<BR/>승인한다.</FONT></TD></TR></TABLE>>,
        likec4_id=admin,
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    admin -> onmaru [arrowhead=normal,
        likec4_id=gqdisv,
        minlen=1,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14"><B>[...]</B></FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ operator initiated ]</FONT></TD></TR></TABLE>>];
    gemini [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Gemini API</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Google AI</FONT></TD></TR></TABLE>>,
        likec4_id=gemini,
        likec4_level=0,
        margin="0.5,0.223",
        width=4.584];
    onmaru -> gemini [arrowhead=normal,
        likec4_id=iy6o5d,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14"><B>[...]</B></FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ HTTPS · no member transcript ]</FONT></TD></TR></TABLE>>];
    observability [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Grafana Cloud</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">공통 trace 조회, metric/dashboard/alerts, 품질 검토</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">OTel / Prometheus compatible</FONT></TD></TR></TABLE>>,
        likec4_id=observability,
        likec4_level=0,
        margin="0.5,0.223",
        width=4.584];
    onmaru -> observability [arrowhead=normal,
        likec4_id="1x0tul9",
        minlen=1,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14"><B>[...]</B></FONT></TD></TR></TABLE>>];
    gemini -> onmaru [arrowhead=normal,
        likec4_id="1f3wnvl",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14"><B>[...]</B></FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ HTTPS ]</FONT></TD></TR></TABLE>>];
}
`;case`service-containers`:return`digraph {
    graph [TBbalance=min,
        bgcolor=transparent,
        compound=true,
        fontname=Arial,
        fontsize=20,
        labeljust=l,
        labelloc=t,
        layout=dot,
        likec4_viewId="service-containers",
        nodesep=0.834,
        outputorder=nodesfirst,
        pad=0.209,
        rankdir=LR,
        ranksep=1.389,
        splines=ortho
    ];
    node [color="#2563eb",
        fillcolor="#3b82f6",
        fontcolor="#eff6ff",
        fontname=Arial,
        label="\\N",
        penwidth=0,
        shape=rect,
        style=filled
    ];
    edge [arrowsize=0.75,
        color="#8D8D8D",
        fontcolor="#C9C9C9",
        fontname=Arial,
        fontsize=14,
        penwidth=2,
        style=""
    ];
    subgraph cluster_onmaru {
        graph [color="#1b3d88",
            fillcolor="#194b9e",
            label=<<FONT POINT-SIZE="11" COLOR="#bfdbfeb3"><B>ONMARU</B></FONT>>,
            likec4_depth=1,
            likec4_id=onmaru,
            likec4_level=0,
            margin=40,
            style=filled
        ];
        spring [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Spring API Server</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">회원 인증·대화·쿼리 권한·정형 SQL·최종 검증·영속화·SSE를 소유한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Spring Boot · 독립 프로세스</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.spring",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        web [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Next.js Web</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">대화 입력, SSE 표시, 장소 카드, 출처, 이어하기 UI.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Next.js · Vercel</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.web",
            likec4_level=1,
            margin="0.278,0.306",
            width=4.445];
        ai [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">FastAPI AI Server</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">비공개 AI API. 질문 해석·route 제안·승인 plan 검색·근거 제한</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Python · 독립 프로세스 · onmaru-ai-engine 저장소</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.ai",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        nginx [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Public API Ingress</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">외부에 80/443만 열고 HTTPS와 SSE를 Spring API로 전달한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Nginx · Lightsail</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.nginx",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        db [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">PostgreSQL</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">업무 schema와 ai schema를 논리·role 권한으로 분리한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">PostGIS + pgvector + Korean full-text</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.db",
            likec4_level=1,
            margin="0.223,0",
            penwidth=2,
            shape=cylinder,
            width=4.445];
    }
    traveler [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">여행자</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">OnMaru 웹에서 대화형 여정 검색을 요청하고 검증된 결과를 받는다.</FONT></TD></TR></TABLE>>,
        likec4_id=traveler,
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    traveler -> web [arrowhead=normal,
        likec4_id=icih69,
        minlen=1,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">대화 질문 입력</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ HTTPS ]</FONT></TD></TR></TABLE>>];
    admin [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">운영자</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Grafana 검토 큐에서 품질 저하 사례를 선택해 격리 실험을 시작하고 승격을<BR/>승인한다.</FONT></TD></TR></TABLE>>,
        likec4_id=admin,
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    admin -> ai [arrowhead=normal,
        likec4_id="18u5t3d",
        minlen=1,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">선택한 품질 사례 조사·격리 실험 시작</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ operator initiated ]</FONT></TD></TR></TABLE>>];
    gemini [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Gemini API</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Google AI</FONT></TD></TR></TABLE>>,
        likec4_id=gemini,
        likec4_level=0,
        margin="0.5,0.223",
        width=4.584];
    gemini -> ai [arrowhead=normal,
        likec4_id="15bpwlj",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">구조화 claim proposal</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ HTTPS ]</FONT></TD></TR></TABLE>>];
    spring -> web [arrowhead=normal,
        likec4_id="1bw92vf",
        style=dashed,
        weight=2,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">저장된 snapshot을 SSE replay</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ SSE · Last-Event-ID ]</FONT></TD></TR></TABLE>>];
    spring -> ai [arrowhead=normal,
        likec4_id=mz4ser,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14"><B>[...]</B></FONT></TD></TR></TABLE>>];
    spring -> db [arrowhead=normal,
        likec4_id=mz4shp,
        style=dashed,
        weight=2,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">정형 사실 조회·대화 저장</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ Spring DB role ]</FONT></TD></TR></TABLE>>];
    observability [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Grafana Cloud</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">공통 trace 조회, metric/dashboard/alerts, 품질 검토</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">OTel / Prometheus compatible</FONT></TD></TR></TABLE>>,
        likec4_id=observability,
        likec4_level=0,
        margin="0.5,0.223",
        width=4.584];
    spring -> observability [arrowhead=normal,
        likec4_id=nikow2,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">root span / low-cardinality metrics</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ OTLP ]</FONT></TD></TR></TABLE>>];
    web -> nginx [arrowhead=normal,
        likec4_id="154jij0",
        style=dashed,
        weight=2,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">API request / SSE connection</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ HTTPS · api.onmaru.site ]</FONT></TD></TR></TABLE>>];
    ai -> gemini [arrowhead=normal,
        likec4_id="15kmsqv",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">근거 제한 생성 요청</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ HTTPS · no member transcript ]</FONT></TD></TR></TABLE>>];
    ai -> spring [arrowhead=normal,
        likec4_id="1pnhv9v",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14"><B>[...]</B></FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ Private HTTP ]</FONT></TD></TR></TABLE>>];
    ai -> db [arrowhead=normal,
        likec4_id="1q3tffo",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">공개 corpus 검색·평가 artifact</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ AI least-privilege DB role ]</FONT></TD></TR></TABLE>>];
    ai -> observability [arrowhead=normal,
        likec4_id=kj01p7,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">child spans / retrieval stage metrics</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ W3C trace context ]</FONT></TD></TR></TABLE>>];
    nginx -> spring [arrowhead=normal,
        likec4_id="7a5eul",
        style=dashed,
        weight=2,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">proxy API / SSE; buffering disabled</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ private Docker network ]</FONT></TD></TR></TABLE>>];
    db -> ai [arrowhead=normal,
        likec4_id=hjdhwk,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14"><B>[...]</B></FONT></TD></TR></TABLE>>];
}
`;case`spring-components`:return`digraph {
    graph [TBbalance=min,
        bgcolor=transparent,
        compound=true,
        fontname=Arial,
        fontsize=20,
        labeljust=l,
        labelloc=t,
        layout=dot,
        likec4_viewId="spring-components",
        nodesep=0.625,
        outputorder=nodesfirst,
        pad=0.209,
        rankdir=TB,
        ranksep=1.112,
        splines=ortho
    ];
    node [color="#2563eb",
        fillcolor="#3b82f6",
        fontcolor="#eff6ff",
        fontname=Arial,
        label="\\N",
        penwidth=0,
        shape=rect,
        style=filled
    ];
    edge [arrowsize=0.75,
        color="#8D8D8D",
        fontcolor="#C9C9C9",
        fontname=Arial,
        fontsize=14,
        penwidth=2,
        style=""
    ];
    subgraph cluster_spring {
        graph [color="#1b3d88",
            fillcolor="#194b9e",
            label=<<FONT POINT-SIZE="11" COLOR="#bfdbfeb3"><B>SPRING API SERVER</B></FONT>>,
            likec4_depth=1,
            likec4_id="onmaru.spring",
            likec4_level=0,
            margin=40,
            style=filled
        ];
        authority [group="onmaru.spring",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Plan Authority Gate</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">route·정형 필드·ID·공개 필터·version을 승인한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">allowlist / hard filters</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.spring.authority",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        finalvalidator [group="onmaru.spring",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Final Validator</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">장소·출처·철회·조건·claim을 다시 검증한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">claim / rights / state</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.spring.finalValidator",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        admission [group="onmaru.spring",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Admission &amp; Conversation</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">소유권, 사용량, 대화 컨텍스트, 멱등성 검사.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">auth / run / state</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.spring.admission",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        sqlexecutor [group="onmaru.spring",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Canonical SQL Executor</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">허용된 정형 사실만 업무 schema에서 조회한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">parameterized SQL</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.spring.sqlExecutor",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        persistence [group="onmaru.spring",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Run Persistence &amp; SSE</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">확정 답변을 저장한 뒤 상태와 답변 조각을 SSE로 전송한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">snapshot / replay</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.spring.persistence",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        privacy [group="onmaru.spring",
            height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Input Privacy Gate</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">원문을 유지하고 AI plan용 비식별 질문을 만든다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">safeQuery</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.spring.privacy",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
    }
    ai [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">FastAPI AI Server</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">비공개 AI API. 질문 해석·route 제안·승인 plan 검색·근거 제한</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Python · 독립 프로세스 · onmaru-ai-engine 저장소</FONT></TD></TR></TABLE>>,
        likec4_id="onmaru.ai",
        likec4_level=0,
        margin="0.5,0.223",
        width=4.584];
    ai -> authority [arrowhead=normal,
        likec4_id="1725wz0",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">PlanProposal</FONT></TD></TR></TABLE>>];
    ai -> finalvalidator [arrowhead=normal,
        likec4_id="1f1re3z",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">ValidatedProposal</FONT></TD></TR></TABLE>>];
    authority -> ai [arrowhead=normal,
        likec4_id=gvovu4,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">approved plan · planHash</FONT></TD></TR></TABLE>>];
    authority -> sqlexecutor [arrowhead=normal,
        likec4_id="1uruynm",
        style=dashed,
        weight=2,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">authorize canonical fields</FONT></TD></TR></TABLE>>];
    finalvalidator -> persistence [arrowhead=normal,
        likec4_id=vu8gun,
        style=dashed,
        weight=2,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">persist validated snapshot</FONT></TD></TR></TABLE>>];
    admission -> privacy [arrowhead=normal,
        likec4_id="6el2it",
        minlen=1,
        style=dashed,
        weight=2,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">load confirmed context · create<BR/>safeQuery</FONT></TD></TR></TABLE>>];
    observability [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Grafana Cloud</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">공통 trace 조회, metric/dashboard/alerts, 품질 검토</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">OTel / Prometheus compatible</FONT></TD></TR></TABLE>>,
        likec4_id=observability,
        likec4_level=0,
        margin="0.5,0.223",
        width=4.584];
    db [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">PostgreSQL</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">업무 schema와 ai schema를 논리·role 권한으로 분리한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">PostGIS + pgvector + Korean full-text</FONT></TD></TR></TABLE>>,
        likec4_id="onmaru.db",
        likec4_level=0,
        margin="0.223,0",
        penwidth=2,
        shape=cylinder,
        width=4.445];
    sqlexecutor -> db [arrowhead=normal,
        likec4_id="1wspquy",
        minlen=1,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">read permitted facts</FONT></TD></TR></TABLE>>];
    persistence -> ai [arrowhead=normal,
        likec4_id="1fsl5be",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">privacy-safe run observation</FONT></TD></TR></TABLE>>];
    web [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Next.js Web</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">대화 입력, SSE 표시, 장소 카드, 출처, 이어하기 UI.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Next.js · Vercel</FONT></TD></TR></TABLE>>,
        likec4_id="onmaru.web",
        likec4_level=0,
        margin="0.278,0.306",
        width=4.445];
    persistence -> web [arrowhead=normal,
        likec4_id="4gp21e",
        minlen=1,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">verified SSE / replay</FONT></TD></TR></TABLE>>];
    privacy -> ai [arrowhead=normal,
        likec4_id="1owyukb",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">plan request · transient safeQuery</FONT></TD></TR></TABLE>>];
    privacy -> observability [arrowhead=normal,
        likec4_id=nikow2,
        ltail=cluster_spring,
        minlen=1,
        style=dashed,
        weight=2,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">root span / low-cardinality metrics</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ OTLP ]</FONT></TD></TR></TABLE>>];
}
`;case`fastapi-components`:return`digraph {
    graph [TBbalance=min,
        bgcolor=transparent,
        compound=true,
        fontname=Arial,
        fontsize=20,
        labeljust=l,
        labelloc=t,
        layout=dot,
        likec4_viewId="fastapi-components",
        nodesep=0.667,
        outputorder=nodesfirst,
        pad=0.209,
        rankdir=TB,
        ranksep=1.25,
        splines=ortho
    ];
    node [color="#2563eb",
        fillcolor="#3b82f6",
        fontcolor="#eff6ff",
        fontname=Arial,
        label="\\N",
        penwidth=0,
        shape=rect,
        style=filled
    ];
    edge [arrowsize=0.75,
        color="#8D8D8D",
        fontcolor="#C9C9C9",
        fontname=Arial,
        fontsize=14,
        penwidth=2,
        style=""
    ];
    subgraph cluster_ai {
        graph [color="#1b3d88",
            fillcolor="#194b9e",
            label=<<FONT POINT-SIZE="11" COLOR="#bfdbfeb3"><B>FASTAPI AI SERVER</B></FONT>>,
            likec4_depth=1,
            likec4_id="onmaru.ai",
            likec4_level=0,
            margin=40,
            style=filled
        ];
        qualityharness [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Quality Harness</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">trace·gold 평가에서 실패를 분류하고 선택된 격리 실험 결과를 만든다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">asynchronous / human controlled</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.ai.qualityHarness",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        planapi [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Plan API</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">safeQuery와 구조화 맥락을 해석하고 PlanProposal을 반환한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">POST /internal/v1/plans</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.ai.planApi",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        executeapi [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Execute API</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">Spring이 승인한 plan hash와 필요한 CanonicalFacts만</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">POST /internal/v1/runs/{id}/execute</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.ai.executeApi",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        corpusworker [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Corpus Worker</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">공개 projection을 파싱·청킹·enrichment·임베딩·색인한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">offline / serialized</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.ai.corpusWorker",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        normalizer [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Query Normalizer</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">동의어·주제·대상·부정·다턴 맥락을 보존한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">alias / polarity / context</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.ai.normalizer",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        planvalidator [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Approved Plan Validator</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">승인 plan·config·corpus·철회 sequence를 검증한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">hash / revision / policy</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.ai.planValidator",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        planner [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Query Planner &amp; Router</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">결정적 route와 조회 제약을 제안한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">SQL / lexical / dense / hybrid / combined</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.ai.planner",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        lexical [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Lexical Retriever</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">한국어 토큰 검색 후보와 rank를 반환한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">exact / alias / BM25</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.ai.lexical",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        dense [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Dense Retriever</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">같은 embedding profile의 query vector로 후보를 반환한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">e5-small 384D / pgvector</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.ai.dense",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        fusion [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Fusion &amp; Ranker</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">두 검색기일 때 RRF, 이후 후보 재순위화를 수행한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">conditional RRF / reranker</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.ai.fusion",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        evidence [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Evidence Selector</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">장소별 출처·revision·본문 span을 고른다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">max 12 chunks</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.ai.evidence",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        prompt [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Prompt Assembler</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">추천·수정·해설·비교 템플릿과 공개 근거만 구성한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">task templates</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.ai.prompt",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        generator [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Grounded Generator</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">근거 기반 구조화 claim을 제안한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Gemini provider adapter</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.ai.generator",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
        proposalvalidator [height=2.5,
            label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Proposal Validator</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">claim별 evidence ID·장소 ID·길이·schema를 검증한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">closed schema / evidence allowlist</FONT></TD></TR></TABLE>>,
            likec4_id="onmaru.ai.proposalValidator",
            likec4_level=1,
            margin="0.5,0.223",
            width=4.584];
    }
    admin [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">운영자</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Grafana 검토 큐에서 품질 저하 사례를 선택해 격리 실험을 시작하고 승격을<BR/>승인한다.</FONT></TD></TR></TABLE>>,
        likec4_id=admin,
        likec4_level=0,
        margin="0.223,0.223",
        width=4.445];
    admin -> qualityharness [arrowhead=normal,
        likec4_id=g9npru,
        minlen=1,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">operator-selected investigation /<BR/>experiment</FONT></TD></TR></TABLE>>];
    gemini [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Gemini API</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Google AI</FONT></TD></TR></TABLE>>,
        likec4_id=gemini,
        likec4_level=0,
        margin="0.5,0.223",
        width=4.584];
    gemini -> generator [arrowhead=normal,
        likec4_id="1q4auje",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">structured proposal</FONT></TD></TR></TABLE>>];
    spring [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Spring API Server</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">회원 인증·대화·쿼리 권한·정형 SQL·최종 검증·영속화·SSE를 소유한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Spring Boot · 독립 프로세스</FONT></TD></TR></TABLE>>,
        likec4_id="onmaru.spring",
        likec4_level=0,
        margin="0.5,0.223",
        width=4.584];
    spring -> qualityharness [arrowhead=normal,
        likec4_id=nbboo0,
        style=dashed,
        weight=2,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">privacy-safe run observation</FONT></TD></TR></TABLE>>];
    spring -> planapi [arrowhead=normal,
        likec4_id=xonpva,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">plan request · transient safeQuery</FONT></TD></TR></TABLE>>];
    spring -> executeapi [arrowhead=normal,
        likec4_id=fcugq,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">approved plan · planHash</FONT></TD></TR></TABLE>>];
    db [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">PostgreSQL</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">업무 schema와 ai schema를 논리·role 권한으로 분리한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">PostGIS + pgvector + Korean full-text</FONT></TD></TR></TABLE>>,
        likec4_id="onmaru.db",
        likec4_level=0,
        margin="0.223,0",
        penwidth=2,
        shape=cylinder,
        width=4.445];
    db -> qualityharness [arrowhead=normal,
        likec4_id=kzrdo7,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">gold set + expected evidence</FONT></TD></TR></TABLE>>];
    db -> corpusworker [arrowhead=normal,
        likec4_id="81fr1w",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">public projection + rights revision</FONT></TD></TR></TABLE>>];
    qualityharness -> db [arrowhead=normal,
        likec4_id="1ttzhiv",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">metrics + review artifact</FONT></TD></TR></TABLE>>];
    planapi -> normalizer [arrowhead=normal,
        likec4_id="1jeb74m",
        style=dashed,
        weight=2,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">normalize</FONT></TD></TR></TABLE>>];
    executeapi -> planvalidator [arrowhead=normal,
        likec4_id=ia9z8g,
        style=dashed,
        weight=2,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">validate approved envelope</FONT></TD></TR></TABLE>>];
    corpusworker -> db [arrowhead=normal,
        likec4_id="1d82438",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">inactive revision → validate → activate</FONT></TD></TR></TABLE>>];
    observability [height=2.5,
        label=<<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Grafana Cloud</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">공통 trace 조회, metric/dashboard/alerts, 품질 검토</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">OTel / Prometheus compatible</FONT></TD></TR></TABLE>>,
        likec4_id=observability,
        likec4_level=0,
        margin="0.5,0.223",
        width=4.584];
    normalizer -> planner [arrowhead=normal,
        likec4_id="1x4dbhz",
        style=dashed,
        weight=2,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">questionFrame</FONT></TD></TR></TABLE>>];
    planvalidator -> lexical [arrowhead=normal,
        likec4_id="1osdj69",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">lexical route when requested</FONT></TD></TR></TABLE>>];
    planvalidator -> dense [arrowhead=normal,
        likec4_id="7nsc3i",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">dense route when requested</FONT></TD></TR></TABLE>>];
    planner -> spring [arrowhead=normal,
        likec4_id="1iepbhz",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">PlanProposal</FONT></TD></TR></TABLE>>];
    lexical -> fusion [arrowhead=normal,
        likec4_id="1rwig0k",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">ranked candidates</FONT></TD></TR></TABLE>>];
    dense -> fusion [arrowhead=normal,
        likec4_id=e0bkyj,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">ranked candidates</FONT></TD></TR></TABLE>>];
    fusion -> evidence [arrowhead=normal,
        likec4_id=sbfnip,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">RRF only for hybrid · rerank</FONT></TD></TR></TABLE>>];
    evidence -> prompt [arrowhead=normal,
        likec4_id="9mn6hp",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">EvidenceSet</FONT></TD></TR></TABLE>>];
    prompt -> generator [arrowhead=normal,
        likec4_id="1u1084d",
        style=dashed,
        weight=3,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">bounded prompt</FONT></TD></TR></TABLE>>];
    generator -> gemini [arrowhead=normal,
        likec4_id=oe84vu,
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">public evidence only</FONT></TD></TR></TABLE>>];
    generator -> proposalvalidator [arrowhead=normal,
        likec4_id="1fnugi3",
        style=dashed,
        weight=3,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">claim + evidence IDs</FONT></TD></TR></TABLE>>];
    proposalvalidator -> spring [arrowhead=normal,
        likec4_id="14u9n4f",
        style=dashed,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">ValidatedProposal</FONT></TD></TR></TABLE>>];
    proposalvalidator -> observability [arrowhead=normal,
        likec4_id=kj01p7,
        ltail=cluster_ai,
        minlen=1,
        style=dashed,
        weight=2,
        xlabel=<<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">child spans / retrieval stage metrics</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ W3C trace context ]</FONT></TD></TR></TABLE>>];
}
`;case`production-deployment`:return`digraph {
  likec4_viewId = "production-deployment";
  bgcolor = "transparent";
  layout = "dot";
  compound = true;
  rankdir = "TB";
  splines = "spline";
  outputorder = "nodesfirst";
  nodesep = 1.806;
  ranksep = 1.806;
  pad = 0.209;
  fontname = "Arial";
  newrank = true;
  clusterrank = "global";
  graph [
    fontsize = 20;
    labeljust = "l";
    labelloc = "t";
  ];
  edge [
    arrowsize = 0.75;
    fontname = "Arial";
    fontsize = 14;
    penwidth = 2;
    color = "#8D8D8D";
    fontcolor = "#C9C9C9";
    style = "dashed";
  ];
  node [
    fontname = "Arial";
    shape = "rect";
    fillcolor = "#3b82f6";
    fontcolor = "#eff6ff";
    color = "#2563eb";
    style = "filled";
    penwidth = 0;
  ];
  "springinstance" [
    likec4_id = "production.aws.lightsail2gb.springProcess.springInstance";
    likec4_level = 2;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Spring API Server</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">회원 인증·대화·쿼리 권한·정형 SQL·최종 검증·영속화·SSE를 소유한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Spring Boot · 독립 프로세스</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "geminiinstance" [
    likec4_id = "production.google.geminiService.geminiInstance";
    likec4_level = 0;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Gemini API</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Google AI</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "webinstance" [
    likec4_id = "production.vercel.webRuntime.webInstance";
    likec4_level = 0;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Next.js Web</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">대화 입력, SSE 표시, 장소 카드, 출처, 이어하기 UI.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Next.js · Vercel</FONT></TD></TR></TABLE>>;
    margin = "0.278,0.306";
    width = 4.445;
    height = 2.5;
  ];
  "nginxinstance" [
    likec4_id = "production.aws.lightsail2gb.nginx.nginxInstance";
    likec4_level = 2;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Public API Ingress</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">외부에 80/443만 열고 HTTPS와 SSE를 Spring API로 전달한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Nginx · Lightsail</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "aiinstance" [
    likec4_id = "production.aws.lightsail2gb.fastapiProcess.aiInstance";
    likec4_level = 2;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">FastAPI AI Server</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">비공개 AI API. 질문 해석·route 제안·승인 plan 검색·근거 제한</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Python · 독립 프로세스 · onmaru-ai-engine 저장소</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "grafanainstance" [
    likec4_id = "production.grafanaCloud.telemetryBackend.grafanaInstance";
    likec4_level = 0;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Grafana Cloud</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">공통 trace 조회, metric/dashboard/alerts, 품질 검토</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">OTel / Prometheus compatible</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "dbinstance" [
    likec4_id = "production.aws.lightsail2gb.postgresProcess.dbInstance";
    likec4_level = 2;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">PostgreSQL</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">업무 schema와 ai schema를 논리·role 권한으로 분리한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">PostGIS + pgvector + Korean full-text</FONT></TD></TR></TABLE>>;
    margin = "0.223,0";
    width = 4.445;
    height = 2.5;
    penwidth = 2;
    shape = "cylinder";
  ];
  subgraph "cluster_aws" {
    likec4_id = "production.aws";
    likec4_level = 0;
    likec4_depth = 2;
    fillcolor = "#1a468d";
    color = "#1c3979";
    style = "filled";
    margin = 32;
    label = <<FONT POINT-SIZE="11" COLOR="#bfdbfeb3"><B>AWS</B></FONT>>;
    subgraph "cluster_lightsail2gb" {
      likec4_id = "production.aws.lightsail2gb";
      likec4_level = 1;
      likec4_depth = 1;
      fillcolor = "#194b9e";
      color = "#1b3d88";
      style = "filled";
      margin = 50;
      label = <<FONT POINT-SIZE="11" COLOR="#bfdbfeb3"><B>LIGHTSAIL2GB</B></FONT>>;
      "springinstance";
      "nginxinstance";
      "aiinstance";
      "dbinstance";
    }
  }
  "webinstance" -> "nginxinstance" [
    likec4_id = "1k1bmqm";
    style = "dashed";
    label = <<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">API request / SSE connection</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ HTTPS · api.onmaru.site ]</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "springinstance" -> "webinstance" [
    likec4_id = "fpw2k5";
    style = "dashed";
    label = <<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14"><B>[...]</B></FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ SSE · Last-Event-ID ]</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "geminiinstance" -> "aiinstance" [
    likec4_id = "s9zj5y";
    style = "dashed";
    label = <<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14"><B>[...]</B></FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ HTTPS ]</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
    arrowtail = "normal";
    dir = "both";
    constraint = false;
  ];
  "springinstance" -> "grafanainstance" [
    likec4_id = "1uvoxlk";
    style = "dashed";
    label = <<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">root span / low-cardinality metrics</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ OTLP ]</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "aiinstance" -> "grafanainstance" [
    likec4_id = "1n0bga0";
    style = "dashed";
    label = <<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">child spans / retrieval stage metrics</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ W3C trace context ]</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "nginxinstance" -> "springinstance" [
    likec4_id = "1aoc7vb";
    style = "dashed";
    weight = 4;
    label = <<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14">proxy API / SSE; buffering disabled</FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ private Docker network ]</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "springinstance" -> "aiinstance" [
    likec4_id = "drumcs";
    style = "dashed";
    weight = 4;
    label = <<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14"><B>[...]</B></FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
    arrowtail = "normal";
    dir = "both";
    constraint = false;
  ];
  "springinstance" -> "dbinstance" [
    likec4_id = "19x5xy9";
    style = "dashed";
    weight = 4;
    label = <<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14"><B>[...]</B></FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ Spring DB role ]</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "aiinstance" -> "dbinstance" [
    likec4_id = "3mtgup";
    style = "dashed";
    weight = 4;
    label = <<TABLE BORDER="0" CELLPADDING="3" CELLSPACING="0" BGCOLOR="#18191BA0"><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="14"><B>[...]</B></FONT></TD></TR><TR><TD ALIGN="TEXT" BALIGN="LEFT"><FONT POINT-SIZE="12">[ AI least-privilege DB role ]</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
    arrowtail = "normal";
    dir = "both";
    constraint = false;
  ];
}`;case`online-rag-sse`:return`digraph {
  likec4_viewId = "online-rag-sse";
  bgcolor = "transparent";
  layout = "dot";
  compound = true;
  rankdir = "LR";
  splines = "spline";
  outputorder = "nodesfirst";
  nodesep = 1.528;
  ranksep = 1.667;
  pad = 0.209;
  fontname = "Arial";
  ordering = "in";
  graph [
    fontsize = 20;
    labeljust = "l";
    labelloc = "t";
  ];
  edge [
    arrowsize = 0.75;
    fontname = "Arial";
    fontsize = 14;
    penwidth = 2;
    color = "#8D8D8D";
    fontcolor = "#C9C9C9";
    style = "dashed";
  ];
  node [
    fontname = "Arial";
    shape = "rect";
    fillcolor = "#3b82f6";
    fontcolor = "#eff6ff";
    color = "#2563eb";
    style = "filled";
    penwidth = 0;
  ];
  "web" [
    likec4_id = "onmaru.web";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Next.js Web</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">대화 입력, SSE 표시, 장소 카드, 출처, 이어하기 UI.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Next.js · Vercel</FONT></TD></TR></TABLE>>;
    margin = "0.278,0.306";
    width = 4.445;
    height = 2.5;
  ];
  "nginx" [
    likec4_id = "onmaru.nginx";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Public API Ingress</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">외부에 80/443만 열고 HTTPS와 SSE를 Spring API로 전달한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Nginx · Lightsail</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "admission" [
    likec4_id = "onmaru.spring.admission";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Admission &amp; Conversation</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">소유권, 사용량, 대화 컨텍스트, 멱등성 검사.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">auth / run / state</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "privacy" [
    likec4_id = "onmaru.spring.privacy";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Input Privacy Gate</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">원문을 유지하고 AI plan용 비식별 질문을 만든다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">safeQuery</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "authority" [
    likec4_id = "onmaru.spring.authority";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Plan Authority Gate</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">route·정형 필드·ID·공개 필터·version을 승인한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">allowlist / hard filters</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "planapi" [
    likec4_id = "onmaru.ai.planApi";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Plan API</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">safeQuery와 구조화 맥락을 해석하고 PlanProposal을 반환한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">POST /internal/v1/plans</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "normalizer" [
    likec4_id = "onmaru.ai.normalizer";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Query Normalizer</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">동의어·주제·대상·부정·다턴 맥락을 보존한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">alias / polarity / context</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "planner" [
    likec4_id = "onmaru.ai.planner";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Query Planner &amp; Router</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">결정적 route와 조회 제약을 제안한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">SQL / lexical / dense / hybrid / combined</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "sqlexecutor" [
    likec4_id = "onmaru.spring.sqlExecutor";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Canonical SQL Executor</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">허용된 정형 사실만 업무 schema에서 조회한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">parameterized SQL</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "businessschema" [
    likec4_id = "onmaru.db.businessSchema";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Business Schema</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">회원·대화·장소·권리의 canonical data.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Spring-owned</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "executeapi" [
    likec4_id = "onmaru.ai.executeApi";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Execute API</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">Spring이 승인한 plan hash와 필요한 CanonicalFacts만</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">POST /internal/v1/runs/{id}/execute</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "planvalidator" [
    likec4_id = "onmaru.ai.planValidator";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Approved Plan Validator</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">승인 plan·config·corpus·철회 sequence를 검증한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">hash / revision / policy</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "lexical" [
    likec4_id = "onmaru.ai.lexical";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Lexical Retriever</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">한국어 토큰 검색 후보와 rank를 반환한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">exact / alias / BM25</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "dense" [
    likec4_id = "onmaru.ai.dense";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Dense Retriever</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">같은 embedding profile의 query vector로 후보를 반환한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">e5-small 384D / pgvector</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "fusion" [
    likec4_id = "onmaru.ai.fusion";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Fusion &amp; Ranker</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">두 검색기일 때 RRF, 이후 후보 재순위화를 수행한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">conditional RRF / reranker</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "evidence" [
    likec4_id = "onmaru.ai.evidence";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Evidence Selector</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">장소별 출처·revision·본문 span을 고른다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">max 12 chunks</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "prompt" [
    likec4_id = "onmaru.ai.prompt";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Prompt Assembler</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">추천·수정·해설·비교 템플릿과 공개 근거만 구성한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">task templates</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "generator" [
    likec4_id = "onmaru.ai.generator";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Grounded Generator</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">근거 기반 구조화 claim을 제안한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Gemini provider adapter</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "finalvalidator" [
    likec4_id = "onmaru.spring.finalValidator";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Final Validator</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">장소·출처·철회·조건·claim을 다시 검증한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">claim / rights / state</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "proposalvalidator" [
    likec4_id = "onmaru.ai.proposalValidator";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Proposal Validator</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">claim별 evidence ID·장소 ID·길이·schema를 검증한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">closed schema / evidence allowlist</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "gemini" [
    likec4_id = "gemini";
    likec4_level = 0;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Gemini API</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Google AI</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "persistence" [
    likec4_id = "onmaru.spring.persistence";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Run Persistence &amp; SSE</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">확정 답변을 저장한 뒤 상태와 답변 조각을 SSE로 전송한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">snapshot / replay</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  subgraph "cluster_onmaru" {
    likec4_id = "onmaru";
    likec4_level = 0;
    likec4_depth = 1;
    fillcolor = "#194b9e";
    color = "#1b3d88";
    style = "filled";
    margin = 40;
    label = <<FONT POINT-SIZE="11" COLOR="#bfdbfeb3"><B>ONMARU</B></FONT>>;
    "web";
    "nginx";
    "admission";
    "privacy";
    "authority";
    "planapi";
    "normalizer";
    "planner";
    "sqlexecutor";
    "businessschema";
    "executeapi";
    "planvalidator";
    "lexical";
    "dense";
    "fusion";
    "evidence";
    "prompt";
    "generator";
    "finalvalidator";
    "proposalvalidator";
    "persistence";
  }
  "web" -> "nginx" [
    likec4_id = "step-01";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>0</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">HTTPS · create run + open SSE<BR/>HTTPS · api.onmaru.site</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "nginx" -> "admission" [
    likec4_id = "step-02";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>1</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">POST /api/v1/journeys/{threadId}/runs</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "admission" -> "privacy" [
    likec4_id = "step-03";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>2</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">authenticate · load confirmed context</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "privacy" -> "planapi" [
    likec4_id = "step-04";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>3</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">POST /internal/v1/plans · safeQuery</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "planapi" -> "normalizer" [
    likec4_id = "step-05";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>4</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">normalize questionFrame</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "normalizer" -> "planner" [
    likec4_id = "step-06";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>5</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">select route · propose constraints</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "authority" -> "planapi" [
    likec4_id = "step-07";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>6</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">PlanProposal</FONT></TD></TR></TABLE>>;
    arrowtail = "normal";
    dir = "back";
  ];
  "authority" -> "sqlexecutor" [
    likec4_id = "step-08";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>7</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">execute permitted fields when route<BR/>needs SQL</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "sqlexecutor" -> "businessschema" [
    likec4_id = "step-09";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>8</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">parameterized SQL · business role</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "authority" -> "executeapi" [
    likec4_id = "step-10";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>9</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">POST /internal/v1/runs/{id}/execute ·<BR/>approved plan</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "executeapi" -> "planvalidator" [
    likec4_id = "step-11";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>10</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">verify planHash ·<BR/>corpus/config/revocation</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "planvalidator" -> "lexical" [
    likec4_id = "step-12";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>11</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">BM25 when route includes lexical</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "planvalidator" -> "dense" [
    likec4_id = "step-13";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>12</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">384D vector when route includes dense</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "lexical" -> "fusion" [
    likec4_id = "step-14";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>13</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">ranked candidates</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "dense" -> "fusion" [
    likec4_id = "step-15";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>14</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">ranked candidates</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "fusion" -> "evidence" [
    likec4_id = "step-16";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>15</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">RRF only when both lists exist · rerank</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "evidence" -> "prompt" [
    likec4_id = "step-17";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>16</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">EvidenceSet · source spans</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "prompt" -> "generator" [
    likec4_id = "step-18";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>17</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">bounded prompt</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "generator" -> "gemini" [
    likec4_id = "step-19";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>18</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">grounded structured generation</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "proposalvalidator" -> "gemini" [
    likec4_id = "step-20";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>19</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">claim/evidence proposal</FONT></TD></TR></TABLE>>;
    arrowtail = "normal";
    dir = "back";
  ];
  "finalvalidator" -> "proposalvalidator" [
    likec4_id = "step-21";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>20</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">ValidatedProposal</FONT></TD></TR></TABLE>>;
    arrowtail = "normal";
    dir = "back";
  ];
  "finalvalidator" -> "persistence" [
    likec4_id = "step-22";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>21</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">rights · claim · filters re-check</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "nginx" -> "persistence" [
    likec4_id = "step-23";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>22</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">verified SSE events / replay</FONT></TD></TR></TABLE>>;
    arrowtail = "normal";
    dir = "back";
  ];
  "web" -> "nginx" [
    likec4_id = "step-24";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>23</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">SSE stream to browser</FONT></TD></TR></TABLE>>;
    arrowtail = "normal";
    dir = "back";
  ];
}`;case`offline-corpus-quality`:return`digraph {
  likec4_viewId = "offline-corpus-quality";
  bgcolor = "transparent";
  layout = "dot";
  compound = true;
  rankdir = "LR";
  splines = "spline";
  outputorder = "nodesfirst";
  nodesep = 1.528;
  ranksep = 1.667;
  pad = 0.209;
  fontname = "Arial";
  ordering = "in";
  graph [
    fontsize = 20;
    labeljust = "l";
    labelloc = "t";
  ];
  edge [
    arrowsize = 0.75;
    fontname = "Arial";
    fontsize = 14;
    penwidth = 2;
    color = "#8D8D8D";
    fontcolor = "#C9C9C9";
    style = "dashed";
  ];
  node [
    fontname = "Arial";
    shape = "rect";
    fillcolor = "#3b82f6";
    fontcolor = "#eff6ff";
    color = "#2563eb";
    style = "filled";
    penwidth = 0;
  ];
  "spring" [
    likec4_id = "onmaru.spring";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Spring API Server</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">회원 인증·대화·쿼리 권한·정형 SQL·최종 검증·영속화·SSE를 소유한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Spring Boot · 독립 프로세스</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "businessschema" [
    likec4_id = "onmaru.db.businessSchema";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Business Schema</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">회원·대화·장소·권리의 canonical data.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Spring-owned</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "corpusworker" [
    likec4_id = "onmaru.ai.corpusWorker";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Corpus Worker</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">공개 projection을 파싱·청킹·enrichment·임베딩·색인한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">offline / serialized</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "aischema" [
    likec4_id = "onmaru.db.aiSchema";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">AI Corpus Schema</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">source/revision/chunk/vector/BM25 metadata와</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">AI least-privilege role</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "admin" [
    likec4_id = "admin";
    likec4_level = 0;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">운영자</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">Grafana 검토 큐에서 품질 저하 사례를 선택해 격리 실험을 시작하고 승격을<BR/>승인한다.</FONT></TD></TR></TABLE>>;
    margin = "0.223,0.223";
    width = 4.445;
    height = 2.5;
  ];
  "qualityharness" [
    likec4_id = "onmaru.ai.qualityHarness";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Quality Harness</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">trace·gold 평가에서 실패를 분류하고 선택된 격리 실험 결과를 만든다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">asynchronous / human controlled</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "evalschema" [
    likec4_id = "onmaru.db.evalSchema";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Evaluation Artifacts</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">dataset hash·expected evidence·version·review</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">access-controlled</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  "planner" [
    likec4_id = "onmaru.ai.planner";
    likec4_level = 1;
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="4"><TR><TD><FONT POINT-SIZE="20">Query Planner &amp; Router</FONT></TD></TR><TR><TD><FONT POINT-SIZE="13" COLOR="#bfdbfe">결정적 route와 조회 제약을 제안한다.</FONT></TD></TR><TR><TD><FONT POINT-SIZE="15" COLOR="#bfdbfe">SQL / lexical / dense / hybrid / combined</FONT></TD></TR></TABLE>>;
    margin = "0.5,0.223";
    width = 4.584;
    height = 2.5;
  ];
  subgraph "cluster_onmaru" {
    likec4_id = "onmaru";
    likec4_level = 0;
    likec4_depth = 1;
    fillcolor = "#194b9e";
    color = "#1b3d88";
    style = "filled";
    margin = 40;
    label = <<FONT POINT-SIZE="11" COLOR="#bfdbfeb3"><B>ONMARU</B></FONT>>;
    "spring";
    "businessschema";
    "corpusworker";
    "aischema";
    "qualityharness";
    "evalschema";
    "planner";
  }
  "spring" -> "corpusworker" [
    likec4_id = "step-01";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>0</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">versioned public projection ·<BR/>rights/revocation</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "corpusworker" -> "aischema" [
    likec4_id = "step-02";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>1</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">parse · chunk · enrich · embed · index<BR/>inactive revision</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "businessschema" -> "corpusworker" [
    likec4_id = "step-03";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>2</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">public-only source manifest</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "qualityharness" -> "evalschema" [
    likec4_id = "step-04";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>3</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">persist run observations · evaluation<BR/>artifacts</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "qualityharness" -> "evalschema" [
    likec4_id = "step-05";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>4</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">gold replay · expected evidence</FONT></TD></TR></TABLE>>;
    arrowtail = "normal";
    dir = "back";
  ];
  "admin" -> "qualityharness" [
    likec4_id = "step-06";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>5</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">select case · start isolated experiment</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
  "qualityharness" -> "planner" [
    likec4_id = "step-07";
    label = <<TABLE BORDER="0" CELLPADDING="0" CELLSPACING="3"><TR><TD><TABLE BORDER="0" CELLPADDING="6" BGCOLOR="#18191BA0"><TR><TD WIDTH="20" HEIGHT="20"><FONT POINT-SIZE="14"><B>6</B></FONT></TD></TR></TABLE></TD><TD BGCOLOR="#18191BA0" CELLPADDING="3"><FONT POINT-SIZE="14">candidate config only after human<BR/>approval</FONT></TD></TR></TABLE>>;
    arrowhead = "normal";
  ];
}`;default:throw Error(`Unknown viewId: `+e)}},t=e=>{switch(e){case`index`:return`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Generated by graphviz version 16.1.0 (0)
 -->
<!-- Pages: 1 -->
<svg width="1055pt" height="896pt"
 viewBox="0.00 0.00 1055.00 896.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(15.05 881.45)">
<!-- traveler -->
<g id="node1" class="node">
<title>traveler</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="441.09,-866.4 9.23,-866.4 9.23,-686.4 441.09,-686.4 441.09,-866.4"/>
<text xml:space="preserve" text-anchor="start" x="200.16" y="-779.4" font-family="Arial" font-size="20.00" fill="#eff6ff">여행자</text>
<text xml:space="preserve" text-anchor="start" x="29.29" y="-756.4" font-family="Arial" font-size="15.00" fill="#bfdbfe">OnMaru 웹에서 대화형 여정 검색을 요청하고 검증된 결과를 받는다.</text>
</g>
<!-- onmaru -->
<g id="node2" class="node">
<title>onmaru</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="666.18,-523.2 346.14,-523.2 346.14,-343.2 666.18,-343.2 666.18,-523.2"/>
<text xml:space="preserve" text-anchor="start" x="470.04" y="-425.2" font-family="Arial" font-size="20.00" fill="#eff6ff">OnMaru</text>
</g>
<!-- admin -->
<g id="node3" class="node">
<title>admin</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1024.94,-866.4 551.39,-866.4 551.39,-686.4 1024.94,-686.4 1024.94,-866.4"/>
<text xml:space="preserve" text-anchor="start" x="763.16" y="-788.4" font-family="Arial" font-size="20.00" fill="#eff6ff">운영자</text>
<text xml:space="preserve" text-anchor="start" x="571.44" y="-765.4" font-family="Arial" font-size="15.00" fill="#bfdbfe">Grafana 검토 큐에서 품질 저하 사례를 선택해 격리 실험을 시작하고 승격을</text>
<text xml:space="preserve" text-anchor="start" x="761.07" y="-747.4" font-family="Arial" font-size="15.00" fill="#bfdbfe">승인한다.</text>
</g>
<!-- gemini -->
<g id="node4" class="node">
<title>gemini</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="412.33,-180 0,-180 0,0 412.33,0 412.33,-180"/>
<text xml:space="preserve" text-anchor="start" x="155.59" y="-102.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Gemini API</text>
<text xml:space="preserve" text-anchor="start" x="40" y="-81.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을</text>
<text xml:space="preserve" text-anchor="start" x="172.81" y="-60.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Google AI</text>
</g>
<!-- observability -->
<g id="node5" class="node">
<title>observability</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="879.52,-180 522.81,-180 522.81,0 879.52,0 879.52,-180"/>
<text xml:space="preserve" text-anchor="start" x="636.12" y="-102.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Grafana Cloud</text>
<text xml:space="preserve" text-anchor="start" x="562.81" y="-81.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">공통 trace 조회, metric/dashboard/alerts, 품질 검토</text>
<text xml:space="preserve" text-anchor="start" x="599.87" y="-60.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">OTel / Prometheus compatible</text>
</g>
<!-- traveler&#45;&gt;onmaru -->
<g id="edge1" class="edge">
<title>traveler&#45;&gt;onmaru</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M298.26,-686.64C337.54,-638.95 386.03,-580.07 426.3,-531.17"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="428.28,-532.9 431.02,-525.44 424.23,-529.56 428.28,-532.9"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="382.49,-583.2 382.49,-626.4 466.28,-626.4 466.28,-583.2 382.49,-583.2"/>
<text xml:space="preserve" text-anchor="start" x="385.49" y="-609.4" font-family="Arial" font-size="14.00" fill="#c9c9c9">대화 질문 입력</text>
<text xml:space="preserve" text-anchor="start" x="385.49" y="-588.6" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ HTTPS ]</text>
</g>
<!-- onmaru&#45;&gt;gemini -->
<g id="edge3" class="edge">
<title>onmaru&#45;&gt;gemini</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M346.43,-397.69C284.69,-375.72 220.24,-340.21 183.78,-283.2 166.31,-255.87 165.2,-221.82 170.6,-190"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="173.16,-190.59 171.99,-182.73 168,-189.6 173.16,-190.59"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="183.78,-240 183.78,-283.2 369.16,-283.2 369.16,-240 183.78,-240"/>
<text xml:space="preserve" text-anchor="start" x="186.78" y="-268.6" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">[...]</text>
<text xml:space="preserve" text-anchor="start" x="186.78" y="-245.4" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ HTTPS · no member transcript ]</text>
</g>
<!-- onmaru&#45;&gt;observability -->
<g id="edge4" class="edge">
<title>onmaru&#45;&gt;observability</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M556.89,-343.44C583.98,-296.04 617.38,-237.6 645.22,-188.88"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="647.41,-190.35 648.85,-182.53 642.85,-187.74 647.41,-190.35"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="615.34,-250.2 615.34,-273 642.33,-273 642.33,-250.2 615.34,-250.2"/>
<text xml:space="preserve" text-anchor="start" x="618.34" y="-258.4" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">[...]</text>
</g>
<!-- admin&#45;&gt;onmaru -->
<g id="edge2" class="edge">
<title>admin&#45;&gt;onmaru</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M714.81,-686.64C675.39,-638.95 626.72,-580.07 586.31,-531.17"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="588.37,-529.55 581.57,-525.44 584.32,-532.89 588.37,-529.55"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="664.05,-583.2 664.05,-626.4 772.77,-626.4 772.77,-583.2 664.05,-583.2"/>
<text xml:space="preserve" text-anchor="start" x="667.05" y="-611.8" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">[...]</text>
<text xml:space="preserve" text-anchor="start" x="667.05" y="-588.6" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ operator initiated ]</text>
</g>
<!-- gemini&#45;&gt;onmaru -->
<g id="edge5" class="edge">
<title>gemini&#45;&gt;onmaru</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M329.91,-179.69C351.93,-198.29 373.71,-218.76 392.16,-240 416.82,-268.37 439.14,-302.8 457.36,-334.64"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="454.93,-335.67 460.9,-340.91 459.5,-333.08 454.93,-335.67"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="422.05,-240 422.05,-283.2 480.72,-283.2 480.72,-240 422.05,-240"/>
<text xml:space="preserve" text-anchor="start" x="425.05" y="-268.6" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">[...]</text>
<text xml:space="preserve" text-anchor="start" x="425.05" y="-245.4" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ HTTPS ]</text>
</g>
</g>
</svg>
`;case`system-context`:return`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Generated by graphviz version 16.1.0 (0)
 -->
<!-- Pages: 1 -->
<svg width="1436pt" height="585pt"
 viewBox="0.00 0.00 1436.00 585.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(15.05 570.05)">
<!-- traveler -->
<g id="node1" class="node">
<title>traveler</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="452.71,-555 20.84,-555 20.84,-375 452.71,-375 452.71,-555"/>
<text xml:space="preserve" text-anchor="start" x="211.77" y="-468" font-family="Arial" font-size="20.00" fill="#eff6ff">여행자</text>
<text xml:space="preserve" text-anchor="start" x="40.9" y="-445" font-family="Arial" font-size="15.00" fill="#bfdbfe">OnMaru 웹에서 대화형 여정 검색을 요청하고 검증된 결과를 받는다.</text>
</g>
<!-- onmaru -->
<g id="node2" class="node">
<title>onmaru</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="893.59,-430 573.55,-430 573.55,-250 893.59,-250 893.59,-430"/>
<text xml:space="preserve" text-anchor="start" x="697.45" y="-332" font-family="Arial" font-size="20.00" fill="#eff6ff">OnMaru</text>
</g>
<!-- admin -->
<g id="node3" class="node">
<title>admin</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="473.55,-305 0,-305 0,-125 473.55,-125 473.55,-305"/>
<text xml:space="preserve" text-anchor="start" x="211.77" y="-227" font-family="Arial" font-size="20.00" fill="#eff6ff">운영자</text>
<text xml:space="preserve" text-anchor="start" x="20.06" y="-204" font-family="Arial" font-size="15.00" fill="#bfdbfe">Grafana 검토 큐에서 품질 저하 사례를 선택해 격리 실험을 시작하고 승격을</text>
<text xml:space="preserve" text-anchor="start" x="209.69" y="-186" font-family="Arial" font-size="15.00" fill="#bfdbfe">승인한다.</text>
</g>
<!-- gemini -->
<g id="node4" class="node">
<title>gemini</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1405.92,-430 993.59,-430 993.59,-250 1405.92,-250 1405.92,-430"/>
<text xml:space="preserve" text-anchor="start" x="1149.18" y="-352.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Gemini API</text>
<text xml:space="preserve" text-anchor="start" x="1033.59" y="-331.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을</text>
<text xml:space="preserve" text-anchor="start" x="1166.4" y="-310.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Google AI</text>
</g>
<!-- observability -->
<g id="node5" class="node">
<title>observability</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1378.11,-180 1021.4,-180 1021.4,0 1378.11,0 1378.11,-180"/>
<text xml:space="preserve" text-anchor="start" x="1134.72" y="-102.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Grafana Cloud</text>
<text xml:space="preserve" text-anchor="start" x="1061.4" y="-81.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">공통 trace 조회, metric/dashboard/alerts, 품질 검토</text>
<text xml:space="preserve" text-anchor="start" x="1098.46" y="-60.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">OTel / Prometheus compatible</text>
</g>
<!-- traveler&#45;&gt;onmaru -->
<g id="edge1" class="edge">
<title>traveler&#45;&gt;onmaru</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M452.51,-402.5C452.51,-402.5 563.24,-402.5 563.24,-402.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="563.24,-405.13 570.74,-402.5 563.24,-399.88 563.24,-405.13"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="507.87,-402.5 507.87,-445.7 591.67,-445.7 591.67,-402.5 507.87,-402.5"/>
<text xml:space="preserve" text-anchor="start" x="510.87" y="-428.7" font-family="Arial" font-size="14.00" fill="#c9c9c9">대화 질문 입력</text>
<text xml:space="preserve" text-anchor="start" x="510.87" y="-407.9" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ HTTPS ]</text>
</g>
<!-- onmaru&#45;&gt;gemini -->
<g id="edge3" class="edge">
<title>onmaru&#45;&gt;gemini</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M893.35,-370C893.35,-370 983.11,-370 983.11,-370"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="983.11,-372.63 990.61,-370 983.11,-367.38 983.11,-372.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="938.23,-326.8 938.23,-370 1123.61,-370 1123.61,-326.8 938.23,-326.8"/>
<text xml:space="preserve" text-anchor="start" x="941.23" y="-355.4" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">[...]</text>
<text xml:space="preserve" text-anchor="start" x="941.23" y="-332.2" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ HTTPS · no member transcript ]</text>
</g>
<!-- onmaru&#45;&gt;observability -->
<g id="edge4" class="edge">
<title>onmaru&#45;&gt;observability</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M733.92,-250.09C733.92,-201.97 733.92,-152.5 733.92,-152.5 733.92,-152.5 1011.12,-152.5 1011.12,-152.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1011.12,-155.13 1018.62,-152.5 1011.12,-149.88 1011.12,-155.13"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="796.73,-129.7 796.73,-152.5 823.72,-152.5 823.72,-129.7 796.73,-129.7"/>
<text xml:space="preserve" text-anchor="start" x="799.73" y="-137.9" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">[...]</text>
</g>
<!-- admin&#45;&gt;onmaru -->
<g id="edge2" class="edge">
<title>admin&#45;&gt;onmaru</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M473.53,-277.5C473.53,-277.5 563.29,-277.5 563.29,-277.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="563.29,-280.13 570.79,-277.5 563.29,-274.88 563.29,-280.13"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="518.41,-234.3 518.41,-277.5 627.14,-277.5 627.14,-234.3 518.41,-234.3"/>
<text xml:space="preserve" text-anchor="start" x="521.41" y="-262.9" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">[...]</text>
<text xml:space="preserve" text-anchor="start" x="521.41" y="-239.7" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ operator initiated ]</text>
</g>
<!-- gemini&#45;&gt;onmaru -->
<g id="edge5" class="edge">
<title>gemini&#45;&gt;onmaru</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M993.92,-310C993.92,-310 904.02,-310 904.02,-310"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="904.02,-307.38 896.52,-310 904.02,-312.63 904.02,-307.38"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="890.3,-266.8 890.3,-310 948.97,-310 948.97,-266.8 890.3,-266.8"/>
<text xml:space="preserve" text-anchor="start" x="893.3" y="-295.4" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">[...]</text>
<text xml:space="preserve" text-anchor="start" x="893.3" y="-272.2" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ HTTPS ]</text>
</g>
</g>
</svg>
`;case`service-containers`:return`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Generated by graphviz version 16.1.0 (0)
 -->
<!-- Pages: 1 -->
<svg width="1614pt" height="1595pt"
 viewBox="0.00 0.00 1614.00 1595.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(15.05 1580.05)">
<g id="clust1" class="cluster">
<title>cluster_onmaru</title>
<polygon fill="#194b9e" stroke="#1b3d88" points="8,-460 8,-1105 1575.82,-1105 1575.82,-460 8,-460"/>
<text xml:space="preserve" text-anchor="start" x="16" y="-1092.1" font-family="Arial" font-weight="bold" font-size="11.00" fill="#bfdbfe" fill-opacity="0.701961">ONMARU</text>
</g>
<!-- spring -->
<g id="node1" class="node">
<title>spring</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="505.09,-831 48,-831 48,-651 505.09,-651 505.09,-831"/>
<text xml:space="preserve" text-anchor="start" x="196.51" y="-753.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Spring API Server</text>
<text xml:space="preserve" text-anchor="start" x="88" y="-732.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">회원 인증·대화·쿼리 권한·정형 SQL·최종 검증·영속화·SSE를 소유한다.</text>
<text xml:space="preserve" text-anchor="start" x="189.43" y="-711.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Spring Boot · 독립 프로세스</text>
</g>
<!-- web -->
<g id="node2" class="node">
<title>web</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="976.25,-1044 656.21,-1044 656.21,-864 976.25,-864 976.25,-1044"/>
<text xml:space="preserve" text-anchor="start" x="762.33" y="-966.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Next.js Web</text>
<text xml:space="preserve" text-anchor="start" x="686.57" y="-945.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">대화 입력, SSE 표시, 장소 카드, 출처, 이어하기 UI.</text>
<text xml:space="preserve" text-anchor="start" x="763.72" y="-924.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Next.js · Vercel</text>
</g>
<!-- ai -->
<g id="node3" class="node">
<title>ai</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1019.15,-680 613.32,-680 613.32,-500 1019.15,-500 1019.15,-680"/>
<text xml:space="preserve" text-anchor="start" x="736.21" y="-602.8" font-family="Arial" font-size="20.00" fill="#eff6ff">FastAPI AI Server</text>
<text xml:space="preserve" text-anchor="start" x="653.32" y="-581.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">비공개 AI API. 질문 해석·route 제안·승인 plan 검색·근거 제한</text>
<text xml:space="preserve" text-anchor="start" x="657" y="-560.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Python · 독립 프로세스 · onmaru&#45;ai&#45;engine 저장소</text>
</g>
<!-- nginx -->
<g id="node4" class="node">
<title>nginx</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1535.82,-1013 1119.15,-1013 1119.15,-833 1535.82,-833 1535.82,-1013"/>
<text xml:space="preserve" text-anchor="start" x="1245.78" y="-935.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Public API Ingress</text>
<text xml:space="preserve" text-anchor="start" x="1159.15" y="-914.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">외부에 80/443만 열고 HTTPS와 SSE를 Spring API로 전달한다.</text>
<text xml:space="preserve" text-anchor="start" x="1272.46" y="-893.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Nginx · Lightsail</text>
</g>
<!-- db -->
<g id="node5" class="node">
<title>db</title>
<path fill="#3b82f6" stroke="#2563eb" stroke-width="2" d="M1501.06,-725.64C1501.06,-734.67 1423.26,-742 1327.48,-742 1231.71,-742 1153.91,-734.67 1153.91,-725.64 1153.91,-725.64 1153.91,-578.36 1153.91,-578.36 1153.91,-569.33 1231.71,-562 1327.48,-562 1423.26,-562 1501.06,-569.33 1501.06,-578.36 1501.06,-578.36 1501.06,-725.64 1501.06,-725.64"/>
<path fill="none" stroke="#2563eb" stroke-width="2" d="M1501.06,-725.64C1501.06,-716.61 1423.26,-709.27 1327.48,-709.27 1231.71,-709.27 1153.91,-716.61 1153.91,-725.64"/>
<text xml:space="preserve" text-anchor="start" x="1273.01" y="-664.8" font-family="Arial" font-size="20.00" fill="#eff6ff">PostgreSQL</text>
<text xml:space="preserve" text-anchor="start" x="1173.96" y="-643.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">업무 schema와 ai schema를 논리·role 권한으로 분리한다.</text>
<text xml:space="preserve" text-anchor="start" x="1203.25" y="-622.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">PostGIS + pgvector + Korean full&#45;text</text>
</g>
<!-- traveler -->
<g id="node6" class="node">
<title>traveler</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="492.48,-1565 60.61,-1565 60.61,-1385 492.48,-1385 492.48,-1565"/>
<text xml:space="preserve" text-anchor="start" x="251.54" y="-1478" font-family="Arial" font-size="20.00" fill="#eff6ff">여행자</text>
<text xml:space="preserve" text-anchor="start" x="80.67" y="-1455" font-family="Arial" font-size="15.00" fill="#bfdbfe">OnMaru 웹에서 대화형 여정 검색을 요청하고 검증된 결과를 받는다.</text>
</g>
<!-- admin -->
<g id="node7" class="node">
<title>admin</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="513.32,-1325 39.77,-1325 39.77,-1145 513.32,-1145 513.32,-1325"/>
<text xml:space="preserve" text-anchor="start" x="251.54" y="-1247" font-family="Arial" font-size="20.00" fill="#eff6ff">운영자</text>
<text xml:space="preserve" text-anchor="start" x="59.82" y="-1224" font-family="Arial" font-size="15.00" fill="#bfdbfe">Grafana 검토 큐에서 품질 저하 사례를 선택해 격리 실험을 시작하고 승격을</text>
<text xml:space="preserve" text-anchor="start" x="249.46" y="-1206" font-family="Arial" font-size="15.00" fill="#bfdbfe">승인한다.</text>
</g>
<!-- gemini -->
<g id="node8" class="node">
<title>gemini</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1533.64,-420 1121.32,-420 1121.32,-240 1533.64,-240 1533.64,-420"/>
<text xml:space="preserve" text-anchor="start" x="1276.91" y="-342.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Gemini API</text>
<text xml:space="preserve" text-anchor="start" x="1161.32" y="-321.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을</text>
<text xml:space="preserve" text-anchor="start" x="1294.13" y="-300.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Google AI</text>
</g>
<!-- observability -->
<g id="node9" class="node">
<title>observability</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1505.84,-180 1149.13,-180 1149.13,0 1505.84,0 1505.84,-180"/>
<text xml:space="preserve" text-anchor="start" x="1262.44" y="-102.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Grafana Cloud</text>
<text xml:space="preserve" text-anchor="start" x="1189.13" y="-81.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">공통 trace 조회, metric/dashboard/alerts, 품질 검토</text>
<text xml:space="preserve" text-anchor="start" x="1226.19" y="-60.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">OTel / Prometheus compatible</text>
</g>
<!-- spring&#45;&gt;web -->
<g id="edge4" class="edge">
<title>spring&#45;&gt;web</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M504.85,-801.33C651.93,-801.33 815.82,-801.33 815.82,-801.33 815.82,-801.33 815.82,-853.78 815.82,-853.78"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="813.19,-853.78 815.82,-861.28 818.44,-853.78 813.19,-853.78"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="686.56,-801.33 686.56,-844.53 873.87,-844.53 873.87,-801.33 686.56,-801.33"/>
<text xml:space="preserve" text-anchor="start" x="689.56" y="-827.53" font-family="Arial" font-size="14.00" fill="#c9c9c9">저장된 snapshot을 SSE replay</text>
<text xml:space="preserve" text-anchor="start" x="689.56" y="-806.73" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ SSE · Last&#45;Event&#45;ID ]</text>
</g>
<!-- spring&#45;&gt;ai -->
<g id="edge5" class="edge">
<title>spring&#45;&gt;ai</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M505.03,-658.25C505.03,-658.25 603.11,-658.25 603.11,-658.25"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="603.11,-660.88 610.61,-658.25 603.11,-655.63 603.11,-660.88"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="527.08,-635.45 527.08,-658.25 554.07,-658.25 554.07,-635.45 527.08,-635.45"/>
<text xml:space="preserve" text-anchor="start" x="530.08" y="-643.65" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">[...]</text>
</g>
<!-- spring&#45;&gt;db -->
<g id="edge6" class="edge">
<title>spring&#45;&gt;db</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M504.91,-711C504.91,-711 1142.75,-711 1142.75,-711"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1142.75,-713.63 1150.25,-711 1142.75,-708.38 1142.75,-713.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="681.69,-711 681.69,-754.2 823.83,-754.2 823.83,-711 681.69,-711"/>
<text xml:space="preserve" text-anchor="start" x="684.69" y="-737.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">정형 사실 조회·대화 저장</text>
<text xml:space="preserve" text-anchor="start" x="684.69" y="-716.4" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ Spring DB role ]</text>
</g>
<!-- spring&#45;&gt;observability -->
<g id="edge7" class="edge">
<title>spring&#45;&gt;observability</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M276.82,-651.27C276.82,-466.35 276.82,-60 276.82,-60 276.82,-60 1138.72,-60 1138.72,-60"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1138.72,-62.63 1146.22,-60 1138.72,-57.38 1138.72,-62.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="198.4,-16.8 198.4,-60 412.14,-60 412.14,-16.8 198.4,-16.8"/>
<text xml:space="preserve" text-anchor="start" x="201.4" y="-43" font-family="Arial" font-size="14.00" fill="#c9c9c9">root span / low&#45;cardinality metrics</text>
<text xml:space="preserve" text-anchor="start" x="201.4" y="-22.2" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ OTLP ]</text>
</g>
<!-- web&#45;&gt;nginx -->
<g id="edge8" class="edge">
<title>web&#45;&gt;nginx</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M976.24,-938.5C976.24,-938.5 1109.02,-938.5 1109.02,-938.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1109.02,-941.13 1116.52,-938.5 1109.02,-935.88 1109.02,-941.13"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1042.63,-938.5 1042.63,-981.7 1233.07,-981.7 1233.07,-938.5 1042.63,-938.5"/>
<text xml:space="preserve" text-anchor="start" x="1045.63" y="-964.7" font-family="Arial" font-size="14.00" fill="#c9c9c9">API request / SSE connection</text>
<text xml:space="preserve" text-anchor="start" x="1045.63" y="-943.9" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ HTTPS · api.onmaru.site ]</text>
</g>
<!-- ai&#45;&gt;spring -->
<g id="edge10" class="edge">
<title>ai&#45;&gt;spring</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M613.35,-665.5C613.35,-665.5 515.33,-665.5 515.33,-665.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="515.33,-662.88 507.83,-665.5 515.33,-668.13 515.33,-662.88"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="564.34,-665.5 564.34,-708.7 655.69,-708.7 655.69,-665.5 564.34,-665.5"/>
<text xml:space="preserve" text-anchor="start" x="567.34" y="-694.1" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">[...]</text>
<text xml:space="preserve" text-anchor="start" x="567.34" y="-670.9" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ Private HTTP ]</text>
</g>
<!-- ai&#45;&gt;db -->
<g id="edge11" class="edge">
<title>ai&#45;&gt;db</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1019.03,-601.33C1019.03,-601.33 1142.48,-601.33 1142.48,-601.33"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1142.48,-603.96 1149.98,-601.33 1142.48,-598.71 1142.48,-603.96"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1080.75,-558.13 1080.75,-601.33 1260.25,-601.33 1260.25,-558.13 1080.75,-558.13"/>
<text xml:space="preserve" text-anchor="start" x="1083.75" y="-584.33" font-family="Arial" font-size="14.00" fill="#c9c9c9">공개 corpus 검색·평가 artifact</text>
<text xml:space="preserve" text-anchor="start" x="1083.75" y="-563.53" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ AI least&#45;privilege DB role ]</text>
</g>
<!-- ai&#45;&gt;gemini -->
<g id="edge9" class="edge">
<title>ai&#45;&gt;gemini</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1018.86,-541.33C1086.89,-541.33 1145.82,-541.33 1145.82,-541.33 1145.82,-541.33 1145.82,-430.46 1145.82,-430.46"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1148.44,-430.46 1145.82,-422.96 1143.19,-430.46 1148.44,-430.46"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1137.78,-498.13 1137.78,-541.33 1323.16,-541.33 1323.16,-498.13 1137.78,-498.13"/>
<text xml:space="preserve" text-anchor="start" x="1140.78" y="-524.33" font-family="Arial" font-size="14.00" fill="#c9c9c9">근거 제한 생성 요청</text>
<text xml:space="preserve" text-anchor="start" x="1140.78" y="-503.53" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ HTTPS · no member transcript ]</text>
</g>
<!-- ai&#45;&gt;observability -->
<g id="edge12" class="edge">
<title>ai&#45;&gt;observability</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M815.82,-500.21C815.82,-363.79 815.82,-120 815.82,-120 815.82,-120 1138.72,-120 1138.72,-120"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1138.72,-122.63 1146.22,-120 1138.72,-117.38 1138.72,-122.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="591.18,-105.46 591.18,-148.66 815.82,-148.66 815.82,-105.46 591.18,-105.46"/>
<text xml:space="preserve" text-anchor="start" x="594.18" y="-131.66" font-family="Arial" font-size="14.00" fill="#c9c9c9">child spans / retrieval stage metrics</text>
<text xml:space="preserve" text-anchor="start" x="594.18" y="-110.86" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ W3C trace context ]</text>
</g>
<!-- nginx&#45;&gt;spring -->
<g id="edge13" class="edge">
<title>nginx&#45;&gt;spring</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1129.82,-833.22C1129.82,-800.63 1129.82,-771.67 1129.82,-771.67 1129.82,-771.67 515.45,-771.67 515.45,-771.67"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="515.45,-769.04 507.95,-771.67 515.45,-774.29 515.45,-769.04"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="853.41,-728.47 853.41,-771.67 1078.09,-771.67 1078.09,-728.47 853.41,-728.47"/>
<text xml:space="preserve" text-anchor="start" x="856.41" y="-754.67" font-family="Arial" font-size="14.00" fill="#c9c9c9">proxy API / SSE; buffering disabled</text>
<text xml:space="preserve" text-anchor="start" x="856.41" y="-733.87" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ private Docker network ]</text>
</g>
<!-- db&#45;&gt;ai -->
<g id="edge14" class="edge">
<title>db&#45;&gt;ai</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1152.97,-640.67C1152.97,-640.67 1029.55,-640.67 1029.55,-640.67"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1029.55,-638.04 1022.05,-640.67 1029.55,-643.29 1029.55,-638.04"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1064.26,-617.87 1064.26,-640.67 1091.26,-640.67 1091.26,-617.87 1064.26,-617.87"/>
<text xml:space="preserve" text-anchor="start" x="1067.26" y="-626.07" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">[...]</text>
</g>
<!-- traveler&#45;&gt;web -->
<g id="edge1" class="edge">
<title>traveler&#45;&gt;web</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M492.39,-1475C642.51,-1475 815.82,-1475 815.82,-1475 815.82,-1475 815.82,-1054.39 815.82,-1054.39"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="818.44,-1054.39 815.82,-1046.89 813.19,-1054.39 818.44,-1054.39"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="732.03,-1383.21 732.03,-1426.41 815.82,-1426.41 815.82,-1383.21 732.03,-1383.21"/>
<text xml:space="preserve" text-anchor="start" x="735.03" y="-1409.41" font-family="Arial" font-size="14.00" fill="#c9c9c9">대화 질문 입력</text>
<text xml:space="preserve" text-anchor="start" x="735.03" y="-1388.61" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ HTTPS ]</text>
</g>
<!-- admin&#45;&gt;ai -->
<g id="edge2" class="edge">
<title>admin&#45;&gt;ai</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M508.82,-1145.29C508.82,-986.55 508.82,-672.75 508.82,-672.75 508.82,-672.75 602.8,-672.75 602.8,-672.75"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="602.8,-675.38 610.3,-672.75 602.8,-670.13 602.8,-675.38"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="300.56,-862.03 300.56,-905.23 508.82,-905.23 508.82,-862.03 300.56,-862.03"/>
<text xml:space="preserve" text-anchor="start" x="303.56" y="-888.23" font-family="Arial" font-size="14.00" fill="#c9c9c9">선택한 품질 사례 조사·격리 실험 시작</text>
<text xml:space="preserve" text-anchor="start" x="303.56" y="-867.43" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ operator initiated ]</text>
</g>
<!-- gemini&#45;&gt;ai -->
<g id="edge3" class="edge">
<title>gemini&#45;&gt;ai</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1137.82,-419.75C1137.82,-469.2 1137.82,-520.67 1137.82,-520.67 1137.82,-520.67 1029.51,-520.67 1029.51,-520.67"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1029.51,-518.04 1022.01,-520.67 1029.51,-523.29 1029.51,-518.04"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="998.97,-477.47 998.97,-520.67 1134.12,-520.67 1134.12,-477.47 998.97,-477.47"/>
<text xml:space="preserve" text-anchor="start" x="1001.97" y="-503.67" font-family="Arial" font-size="14.00" fill="#c9c9c9">구조화 claim proposal</text>
<text xml:space="preserve" text-anchor="start" x="1001.97" y="-482.87" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ HTTPS ]</text>
</g>
</g>
</svg>
`;case`spring-components`:return`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Generated by graphviz version 16.1.0 (0)
 -->
<!-- Pages: 1 -->
<svg width="1699pt" height="799pt"
 viewBox="0.00 0.00 1699.00 799.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(15.05 784.25)">
<g id="clust1" class="cluster">
<title>cluster_spring</title>
<polygon fill="#194b9e" stroke="#1b3d88" points="8,-220 8,-761.2 1223,-761.2 1223,-220 8,-220"/>
<text xml:space="preserve" text-anchor="start" x="16" y="-748.3" font-family="Arial" font-weight="bold" font-size="11.00" fill="#bfdbfe" fill-opacity="0.701961">SPRING API SERVER</text>
</g>
<!-- authority -->
<g id="node1" class="node">
<title>authority</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="396.37,-700 47.63,-700 47.63,-520 396.37,-520 396.37,-700"/>
<text xml:space="preserve" text-anchor="start" x="135.29" y="-622.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Plan Authority Gate</text>
<text xml:space="preserve" text-anchor="start" x="87.63" y="-601.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">route·정형 필드·ID·공개 필터·version을 승인한다.</text>
<text xml:space="preserve" text-anchor="start" x="154.48" y="-580.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">allowlist / hard filters</text>
</g>
<!-- finalvalidator -->
<g id="node2" class="node">
<title>finalvalidator</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="785.02,-700 454.98,-700 454.98,-520 785.02,-520 785.02,-700"/>
<text xml:space="preserve" text-anchor="start" x="556.08" y="-622.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Final Validator</text>
<text xml:space="preserve" text-anchor="start" x="503.7" y="-601.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">장소·출처·철회·조건·claim을 다시 검증한다.</text>
<text xml:space="preserve" text-anchor="start" x="555.4" y="-580.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">claim / rights / state</text>
</g>
<!-- admission -->
<g id="node3" class="node">
<title>admission</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1183.02,-700 852.98,-700 852.98,-520 1183.02,-520 1183.02,-700"/>
<text xml:space="preserve" text-anchor="start" x="900.72" y="-622.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Admission &amp; Conversation</text>
<text xml:space="preserve" text-anchor="start" x="909.65" y="-601.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">소유권, 사용량, 대화 컨텍스트, 멱등성 검사.</text>
<text xml:space="preserve" text-anchor="start" x="963.8" y="-580.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">auth / run / state</text>
</g>
<!-- sqlexecutor -->
<g id="node4" class="node">
<title>sqlexecutor</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="387.02,-440 56.98,-440 56.98,-260 387.02,-260 387.02,-440"/>
<text xml:space="preserve" text-anchor="start" x="112.5" y="-362.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Canonical SQL Executor</text>
<text xml:space="preserve" text-anchor="start" x="101.72" y="-341.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">허용된 정형 사실만 업무 schema에서 조회한다.</text>
<text xml:space="preserve" text-anchor="start" x="156.97" y="-320.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">parameterized SQL</text>
</g>
<!-- persistence -->
<g id="node5" class="node">
<title>persistence</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="808.45,-440 431.55,-440 431.55,-260 808.45,-260 808.45,-440"/>
<text xml:space="preserve" text-anchor="start" x="514.39" y="-362.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Run Persistence &amp; SSE</text>
<text xml:space="preserve" text-anchor="start" x="471.55" y="-341.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">확정 답변을 저장한 뒤 상태와 답변 조각을 SSE로 전송한다.</text>
<text xml:space="preserve" text-anchor="start" x="562.88" y="-320.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">snapshot / replay</text>
</g>
<!-- privacy -->
<g id="node6" class="node">
<title>privacy</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1183.02,-440 852.98,-440 852.98,-260 1183.02,-260 1183.02,-440"/>
<text xml:space="preserve" text-anchor="start" x="935.74" y="-362.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Input Privacy Gate</text>
<text xml:space="preserve" text-anchor="start" x="894.83" y="-341.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">원문을 유지하고 AI plan용 비식별 질문을 만든다.</text>
<text xml:space="preserve" text-anchor="start" x="983.4" y="-320.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">safeQuery</text>
</g>
<!-- ai -->
<g id="node7" class="node">
<title>ai</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1668.91,-440 1263.09,-440 1263.09,-260 1668.91,-260 1668.91,-440"/>
<text xml:space="preserve" text-anchor="start" x="1385.98" y="-362.8" font-family="Arial" font-size="20.00" fill="#eff6ff">FastAPI AI Server</text>
<text xml:space="preserve" text-anchor="start" x="1303.09" y="-341.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">비공개 AI API. 질문 해석·route 제안·승인 plan 검색·근거 제한</text>
<text xml:space="preserve" text-anchor="start" x="1306.77" y="-320.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Python · 독립 프로세스 · onmaru&#45;ai&#45;engine 저장소</text>
</g>
<!-- observability -->
<g id="node8" class="node">
<title>observability</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1196.35,-180 839.65,-180 839.65,0 1196.35,0 1196.35,-180"/>
<text xml:space="preserve" text-anchor="start" x="952.96" y="-102.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Grafana Cloud</text>
<text xml:space="preserve" text-anchor="start" x="879.65" y="-81.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">공통 trace 조회, metric/dashboard/alerts, 품질 검토</text>
<text xml:space="preserve" text-anchor="start" x="916.71" y="-60.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">OTel / Prometheus compatible</text>
</g>
<!-- db -->
<g id="node9" class="node">
<title>db</title>
<path fill="#3b82f6" stroke="#2563eb" stroke-width="2" d="M395.57,-163.64C395.57,-172.67 317.78,-180 222,-180 126.22,-180 48.43,-172.67 48.43,-163.64 48.43,-163.64 48.43,-16.36 48.43,-16.36 48.43,-7.33 126.22,0 222,0 317.78,0 395.57,-7.33 395.57,-16.36 395.57,-16.36 395.57,-163.64 395.57,-163.64"/>
<path fill="none" stroke="#2563eb" stroke-width="2" d="M395.57,-163.64C395.57,-154.61 317.78,-147.27 222,-147.27 126.22,-147.27 48.43,-154.61 48.43,-163.64"/>
<text xml:space="preserve" text-anchor="start" x="167.53" y="-102.8" font-family="Arial" font-size="20.00" fill="#eff6ff">PostgreSQL</text>
<text xml:space="preserve" text-anchor="start" x="68.48" y="-81.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">업무 schema와 ai schema를 논리·role 권한으로 분리한다.</text>
<text xml:space="preserve" text-anchor="start" x="97.77" y="-60.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">PostGIS + pgvector + Korean full&#45;text</text>
</g>
<!-- web -->
<g id="node10" class="node">
<title>web</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="780.02,-180 459.98,-180 459.98,0 780.02,0 780.02,-180"/>
<text xml:space="preserve" text-anchor="start" x="566.1" y="-102.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Next.js Web</text>
<text xml:space="preserve" text-anchor="start" x="490.33" y="-81.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">대화 입력, SSE 표시, 장소 카드, 출처, 이어하기 UI.</text>
<text xml:space="preserve" text-anchor="start" x="567.49" y="-60.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Next.js · Vercel</text>
</g>
<!-- authority&#45;&gt;sqlexecutor -->
<g id="edge4" class="edge">
<title>authority&#45;&gt;sqlexecutor</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M222,-520.16C222,-520.16 222,-450.37 222,-450.37"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="224.63,-450.37 222,-442.87 219.38,-450.37 224.63,-450.37"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="58.79,-485.27 58.79,-508.07 222,-508.07 222,-485.27 58.79,-485.27"/>
<text xml:space="preserve" text-anchor="start" x="61.79" y="-491.07" font-family="Arial" font-size="14.00" fill="#c9c9c9">authorize canonical fields</text>
</g>
<!-- authority&#45;&gt;ai -->
<g id="edge3" class="edge">
<title>authority&#45;&gt;ai</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M392.72,-520.05C392.72,-501.77 392.72,-488 392.72,-488 392.72,-488 1587.75,-488 1587.75,-488 1587.75,-488 1587.75,-450.26 1587.75,-450.26"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1590.37,-450.26 1587.75,-442.76 1585.12,-450.26 1590.37,-450.26"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="823.63,-488 823.63,-510.8 993.08,-510.8 993.08,-488 823.63,-488"/>
<text xml:space="preserve" text-anchor="start" x="826.63" y="-493.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">approved plan · planHash</text>
</g>
<!-- finalvalidator&#45;&gt;persistence -->
<g id="edge5" class="edge">
<title>finalvalidator&#45;&gt;persistence</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M564.99,-520.16C564.99,-520.16 564.99,-450.37 564.99,-450.37"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="567.62,-450.37 564.99,-442.87 562.37,-450.37 567.62,-450.37"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="397.12,-485.27 397.12,-508.07 564.99,-508.07 564.99,-485.27 397.12,-485.27"/>
<text xml:space="preserve" text-anchor="start" x="400.12" y="-491.07" font-family="Arial" font-size="14.00" fill="#c9c9c9">persist validated snapshot</text>
</g>
<!-- admission&#45;&gt;privacy -->
<g id="edge6" class="edge">
<title>admission&#45;&gt;privacy</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1018,-520.16C1018,-520.16 1018,-450.37 1018,-450.37"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1020.63,-450.37 1018,-442.87 1015.38,-450.37 1020.63,-450.37"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="917.34,-445.67 917.34,-485.27 1118.66,-485.27 1118.66,-445.67 917.34,-445.67"/>
<text xml:space="preserve" text-anchor="start" x="920.34" y="-468.27" font-family="Arial" font-size="14.00" fill="#c9c9c9">load confirmed context · create</text>
<text xml:space="preserve" text-anchor="start" x="920.34" y="-451.47" font-family="Arial" font-size="14.00" fill="#c9c9c9">safeQuery</text>
</g>
<!-- sqlexecutor&#45;&gt;db -->
<g id="edge7" class="edge">
<title>sqlexecutor&#45;&gt;db</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M222,-260.16C222,-260.16 222,-191.25 222,-191.25"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="224.63,-191.25 222,-183.75 219.38,-191.25 224.63,-191.25"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="92.28,-225.71 92.28,-248.51 222,-248.51 222,-225.71 92.28,-225.71"/>
<text xml:space="preserve" text-anchor="start" x="95.28" y="-231.51" font-family="Arial" font-size="14.00" fill="#c9c9c9">read permitted facts</text>
</g>
<!-- persistence&#45;&gt;ai -->
<g id="edge8" class="edge">
<title>persistence&#45;&gt;ai</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M796.74,-439.9C796.74,-449.58 796.74,-456 796.74,-456 796.74,-456 1506.58,-456 1506.58,-456 1506.58,-456 1506.58,-450.43 1506.58,-450.43"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1509.21,-450.43 1506.58,-442.93 1503.96,-450.43 1509.21,-450.43"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1146.4,-456 1146.4,-478.8 1328.26,-478.8 1328.26,-456 1146.4,-456"/>
<text xml:space="preserve" text-anchor="start" x="1149.4" y="-461.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">privacy&#45;safe run observation</text>
</g>
<!-- persistence&#45;&gt;web -->
<g id="edge9" class="edge">
<title>persistence&#45;&gt;web</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M620,-260.16C620,-260.16 620,-190.37 620,-190.37"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="622.63,-190.37 620,-182.87 617.38,-190.37 622.63,-190.37"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="487.17,-225.27 487.17,-248.07 620,-248.07 620,-225.27 487.17,-225.27"/>
<text xml:space="preserve" text-anchor="start" x="490.17" y="-231.07" font-family="Arial" font-size="14.00" fill="#c9c9c9">verified SSE / replay</text>
</g>
<!-- privacy&#45;&gt;ai -->
<g id="edge10" class="edge">
<title>privacy&#45;&gt;ai</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1182.91,-350C1182.91,-350 1252.88,-350 1252.88,-350"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1252.88,-352.63 1260.38,-350 1252.88,-347.38 1252.88,-352.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1107.5,-327.2 1107.5,-350 1328.29,-350 1328.29,-327.2 1107.5,-327.2"/>
<text xml:space="preserve" text-anchor="start" x="1110.5" y="-333" font-family="Arial" font-size="14.00" fill="#c9c9c9">plan request · transient safeQuery</text>
</g>
<!-- privacy&#45;&gt;observability -->
<g id="edge11" class="edge">
<title>privacy&#45;&gt;observability</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1018,-220C1018,-204.48 1018,-190.37 1018,-190.37"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1020.63,-190.37 1018,-182.87 1015.38,-190.37 1020.63,-190.37"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="804.26,-205.19 804.26,-248.39 1018,-248.39 1018,-205.19 804.26,-205.19"/>
<text xml:space="preserve" text-anchor="start" x="807.26" y="-231.39" font-family="Arial" font-size="14.00" fill="#c9c9c9">root span / low&#45;cardinality metrics</text>
<text xml:space="preserve" text-anchor="start" x="807.26" y="-210.59" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ OTLP ]</text>
</g>
<!-- ai&#45;&gt;authority -->
<g id="edge1" class="edge">
<title>ai&#45;&gt;authority</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1344.25,-439.95C1344.25,-458.23 1344.25,-472 1344.25,-472 1344.25,-472 389.87,-472 389.87,-472 389.87,-472 389.87,-509.74 389.87,-509.74"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="387.25,-509.74 389.87,-517.24 392.5,-509.74 387.25,-509.74"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="774.95,-449.2 774.95,-472 864.22,-472 864.22,-449.2 774.95,-449.2"/>
<text xml:space="preserve" text-anchor="start" x="777.95" y="-455" font-family="Arial" font-size="14.00" fill="#c9c9c9">PlanProposal</text>
</g>
<!-- ai&#45;&gt;finalvalidator -->
<g id="edge2" class="edge">
<title>ai&#45;&gt;finalvalidator</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1425.42,-439.58C1425.42,-473.46 1425.42,-504 1425.42,-504 1425.42,-504 675.01,-504 675.01,-504 675.01,-504 675.01,-509.57 675.01,-509.57"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="672.38,-509.57 675.01,-517.07 677.63,-509.57 672.38,-509.57"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1079.64,-481.2 1079.64,-504 1199.27,-504 1199.27,-481.2 1079.64,-481.2"/>
<text xml:space="preserve" text-anchor="start" x="1082.64" y="-487" font-family="Arial" font-size="14.00" fill="#c9c9c9">ValidatedProposal</text>
</g>
</g>
</svg>
`;case`fastapi-components`:return`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Generated by graphviz version 16.1.0 (0)
 -->
<!-- Pages: 1 -->
<svg width="2708pt" height="2640pt"
 viewBox="0.00 0.00 2708.00 2640.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(15.05 2625.05)">
<g id="clust1" class="cluster">
<title>cluster_ai</title>
<polygon fill="#194b9e" stroke="#1b3d88" points="452.16,-230 452.16,-2401.2 2290.16,-2401.2 2290.16,-230 452.16,-230"/>
<text xml:space="preserve" text-anchor="start" x="460.16" y="-2388.3" font-family="Arial" font-weight="bold" font-size="11.00" fill="#bfdbfe" fill-opacity="0.701961">FASTAPI AI SERVER</text>
</g>
<!-- qualityharness -->
<g id="node1" class="node">
<title>qualityharness</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1809.79,-2340 1376.53,-2340 1376.53,-2160 1809.79,-2160 1809.79,-2340"/>
<text xml:space="preserve" text-anchor="start" x="1522.02" y="-2262.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Quality Harness</text>
<text xml:space="preserve" text-anchor="start" x="1416.53" y="-2241.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">trace·gold 평가에서 실패를 분류하고 선택된 격리 실험 결과를 만든다.</text>
<text xml:space="preserve" text-anchor="start" x="1482.68" y="-2220.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">asynchronous / human controlled</text>
</g>
<!-- planapi -->
<g id="node2" class="node">
<title>planapi</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1328.33,-2340 915.99,-2340 915.99,-2160 1328.33,-2160 1328.33,-2340"/>
<text xml:space="preserve" text-anchor="start" x="1083.25" y="-2262.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Plan API</text>
<text xml:space="preserve" text-anchor="start" x="955.99" y="-2241.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">safeQuery와 구조화 맥락을 해석하고 PlanProposal을 반환한다.</text>
<text xml:space="preserve" text-anchor="start" x="1042.96" y="-2220.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">POST /internal/v1/plans</text>
</g>
<!-- executeapi -->
<g id="node3" class="node">
<title>executeapi</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="867.92,-2340 492.4,-2340 492.4,-2160 867.92,-2160 867.92,-2340"/>
<text xml:space="preserve" text-anchor="start" x="625.13" y="-2262.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Execute API</text>
<text xml:space="preserve" text-anchor="start" x="532.4" y="-2241.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">Spring이 승인한 plan hash와 필요한 CanonicalFacts만</text>
<text xml:space="preserve" text-anchor="start" x="563.02" y="-2220.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">POST /internal/v1/runs/{id}/execute</text>
</g>
<!-- corpusworker -->
<g id="node4" class="node">
<title>corpusworker</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="2250.21,-2340 1858.11,-2340 1858.11,-2160 2250.21,-2160 2250.21,-2340"/>
<text xml:space="preserve" text-anchor="start" x="1986.93" y="-2262.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Corpus Worker</text>
<text xml:space="preserve" text-anchor="start" x="1898.11" y="-2241.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">공개 projection을 파싱·청킹·enrichment·임베딩·색인한다.</text>
<text xml:space="preserve" text-anchor="start" x="1996.22" y="-2220.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">offline / serialized</text>
</g>
<!-- normalizer -->
<g id="node5" class="node">
<title>normalizer</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1468.19,-2070 1138.14,-2070 1138.14,-1890 1468.19,-1890 1468.19,-2070"/>
<text xml:space="preserve" text-anchor="start" x="1224.81" y="-1992.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Query Normalizer</text>
<text xml:space="preserve" text-anchor="start" x="1185.78" y="-1971.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">동의어·주제·대상·부정·다턴 맥락을 보존한다.</text>
<text xml:space="preserve" text-anchor="start" x="1226.88" y="-1950.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">alias / polarity / context</text>
</g>
<!-- planvalidator -->
<g id="node6" class="node">
<title>planvalidator</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="864.31,-2070 496.01,-2070 496.01,-1890 864.31,-1890 864.31,-2070"/>
<text xml:space="preserve" text-anchor="start" x="572.32" y="-1992.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Approved Plan Validator</text>
<text xml:space="preserve" text-anchor="start" x="536.01" y="-1971.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">승인 plan·config·corpus·철회 sequence를 검증한다.</text>
<text xml:space="preserve" text-anchor="start" x="606.38" y="-1950.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">hash / revision / policy</text>
</g>
<!-- planner -->
<g id="node7" class="node">
<title>planner</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1658.4,-1800 1309.93,-1800 1309.93,-1620 1658.4,-1620 1658.4,-1800"/>
<text xml:space="preserve" text-anchor="start" x="1377.44" y="-1722.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Query Planner &amp; Router</text>
<text xml:space="preserve" text-anchor="start" x="1389.89" y="-1701.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">결정적 route와 조회 제약을 제안한다.</text>
<text xml:space="preserve" text-anchor="start" x="1349.93" y="-1680.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">SQL / lexical / dense / hybrid / combined</text>
</g>
<!-- lexical -->
<g id="node8" class="node">
<title>lexical</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="822.19,-1800 492.14,-1800 492.14,-1620 822.19,-1620 822.19,-1800"/>
<text xml:space="preserve" text-anchor="start" x="582.69" y="-1722.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Lexical Retriever</text>
<text xml:space="preserve" text-anchor="start" x="552.42" y="-1701.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">한국어 토큰 검색 후보와 rank를 반환한다.</text>
<text xml:space="preserve" text-anchor="start" x="591.72" y="-1680.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">exact / alias / BM25</text>
</g>
<!-- dense -->
<g id="node9" class="node">
<title>dense</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1262.23,-1800 870.1,-1800 870.1,-1620 1262.23,-1620 1262.23,-1800"/>
<text xml:space="preserve" text-anchor="start" x="993.91" y="-1722.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Dense Retriever</text>
<text xml:space="preserve" text-anchor="start" x="910.1" y="-1701.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">같은 embedding profile의 query vector로 후보를 반환한다.</text>
<text xml:space="preserve" text-anchor="start" x="982.79" y="-1680.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">e5&#45;small 384D / pgvector</text>
</g>
<!-- fusion -->
<g id="node10" class="node">
<title>fusion</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1046.71,-1530 701.61,-1530 701.61,-1350 1046.71,-1350 1046.71,-1530"/>
<text xml:space="preserve" text-anchor="start" x="799.69" y="-1452.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Fusion &amp; Ranker</text>
<text xml:space="preserve" text-anchor="start" x="741.61" y="-1431.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">두 검색기일 때 RRF, 이후 후보 재순위화를 수행한다.</text>
<text xml:space="preserve" text-anchor="start" x="786.63" y="-1410.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">conditional RRF / reranker</text>
</g>
<!-- evidence -->
<g id="node11" class="node">
<title>evidence</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1039.19,-1260 709.14,-1260 709.14,-1080 1039.19,-1080 1039.19,-1260"/>
<text xml:space="preserve" text-anchor="start" x="793.56" y="-1182.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Evidence Selector</text>
<text xml:space="preserve" text-anchor="start" x="763.63" y="-1161.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">장소별 출처·revision·본문 span을 고른다.</text>
<text xml:space="preserve" text-anchor="start" x="823.72" y="-1140.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">max 12 chunks</text>
</g>
<!-- prompt -->
<g id="node12" class="node">
<title>prompt</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1047.8,-990 700.53,-990 700.53,-810 1047.8,-810 1047.8,-990"/>
<text xml:space="preserve" text-anchor="start" x="791.92" y="-912.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Prompt Assembler</text>
<text xml:space="preserve" text-anchor="start" x="740.53" y="-891.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">추천·수정·해설·비교 템플릿과 공개 근거만 구성한다.</text>
<text xml:space="preserve" text-anchor="start" x="825.81" y="-870.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">task templates</text>
</g>
<!-- generator -->
<g id="node13" class="node">
<title>generator</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1039.19,-720 709.14,-720 709.14,-540 1039.19,-540 1039.19,-720"/>
<text xml:space="preserve" text-anchor="start" x="781.88" y="-642.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Grounded Generator</text>
<text xml:space="preserve" text-anchor="start" x="784.95" y="-621.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">근거 기반 구조화 claim을 제안한다.</text>
<text xml:space="preserve" text-anchor="start" x="793.71" y="-600.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Gemini provider adapter</text>
</g>
<!-- proposalvalidator -->
<g id="node14" class="node">
<title>proposalvalidator</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1065.15,-450 683.17,-450 683.17,-270 1065.15,-270 1065.15,-450"/>
<text xml:space="preserve" text-anchor="start" x="792.45" y="-372.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Proposal Validator</text>
<text xml:space="preserve" text-anchor="start" x="723.17" y="-351.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">claim별 evidence ID·장소 ID·길이·schema를 검증한다.</text>
<text xml:space="preserve" text-anchor="start" x="759.52" y="-330.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">closed schema / evidence allowlist</text>
</g>
<!-- admin -->
<g id="node15" class="node">
<title>admin</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1316.94,-2610 843.39,-2610 843.39,-2430 1316.94,-2430 1316.94,-2610"/>
<text xml:space="preserve" text-anchor="start" x="1055.16" y="-2532" font-family="Arial" font-size="20.00" fill="#eff6ff">운영자</text>
<text xml:space="preserve" text-anchor="start" x="863.44" y="-2509" font-family="Arial" font-size="15.00" fill="#bfdbfe">Grafana 검토 큐에서 품질 저하 사례를 선택해 격리 실험을 시작하고 승격을</text>
<text xml:space="preserve" text-anchor="start" x="1053.07" y="-2491" font-family="Arial" font-size="15.00" fill="#bfdbfe">승인한다.</text>
</g>
<!-- gemini -->
<g id="node16" class="node">
<title>gemini</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="412.33,-450 0,-450 0,-270 412.33,-270 412.33,-450"/>
<text xml:space="preserve" text-anchor="start" x="155.59" y="-372.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Gemini API</text>
<text xml:space="preserve" text-anchor="start" x="40" y="-351.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을</text>
<text xml:space="preserve" text-anchor="start" x="172.81" y="-330.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Google AI</text>
</g>
<!-- spring -->
<g id="node17" class="node">
<title>spring</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1821.71,-2610 1364.62,-2610 1364.62,-2430 1821.71,-2430 1821.71,-2610"/>
<text xml:space="preserve" text-anchor="start" x="1513.13" y="-2532.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Spring API Server</text>
<text xml:space="preserve" text-anchor="start" x="1404.62" y="-2511.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">회원 인증·대화·쿼리 권한·정형 SQL·최종 검증·영속화·SSE를 소유한다.</text>
<text xml:space="preserve" text-anchor="start" x="1506.04" y="-2490.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Spring Boot · 독립 프로세스</text>
</g>
<!-- db -->
<g id="node18" class="node">
<title>db</title>
<path fill="#3b82f6" stroke="#2563eb" stroke-width="2" d="M2677.74,-2053.64C2677.74,-2062.67 2599.94,-2070 2504.16,-2070 2408.39,-2070 2330.59,-2062.67 2330.59,-2053.64 2330.59,-2053.64 2330.59,-1906.36 2330.59,-1906.36 2330.59,-1897.33 2408.39,-1890 2504.16,-1890 2599.94,-1890 2677.74,-1897.33 2677.74,-1906.36 2677.74,-1906.36 2677.74,-2053.64 2677.74,-2053.64"/>
<path fill="none" stroke="#2563eb" stroke-width="2" d="M2677.74,-2053.64C2677.74,-2044.61 2599.94,-2037.27 2504.16,-2037.27 2408.39,-2037.27 2330.59,-2044.61 2330.59,-2053.64"/>
<text xml:space="preserve" text-anchor="start" x="2449.69" y="-1992.8" font-family="Arial" font-size="20.00" fill="#eff6ff">PostgreSQL</text>
<text xml:space="preserve" text-anchor="start" x="2350.64" y="-1971.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">업무 schema와 ai schema를 논리·role 권한으로 분리한다.</text>
<text xml:space="preserve" text-anchor="start" x="2379.93" y="-1950.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">PostGIS + pgvector + Korean full&#45;text</text>
</g>
<!-- observability -->
<g id="node19" class="node">
<title>observability</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1052.52,-180 695.81,-180 695.81,0 1052.52,0 1052.52,-180"/>
<text xml:space="preserve" text-anchor="start" x="809.12" y="-102.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Grafana Cloud</text>
<text xml:space="preserve" text-anchor="start" x="735.81" y="-81.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">공통 trace 조회, metric/dashboard/alerts, 품질 검토</text>
<text xml:space="preserve" text-anchor="start" x="772.87" y="-60.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">OTel / Prometheus compatible</text>
</g>
<!-- qualityharness&#45;&gt;db -->
<g id="edge8" class="edge">
<title>qualityharness&#45;&gt;db</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1759.33,-2160.29C1759.33,-2092.12 1759.33,-2010 1759.33,-2010 1759.33,-2010 2319.47,-2010 2319.47,-2010"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="2319.47,-2012.63 2326.97,-2010 2319.47,-2007.38 2319.47,-2012.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1810.83,-2010 1810.83,-2032.8 1964.26,-2032.8 1964.26,-2010 1810.83,-2010"/>
<text xml:space="preserve" text-anchor="start" x="1813.83" y="-2015.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">metrics + review artifact</text>
</g>
<!-- planapi&#45;&gt;normalizer -->
<g id="edge9" class="edge">
<title>planapi&#45;&gt;normalizer</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1233.24,-2160.09C1233.24,-2160.09 1233.24,-2080.5 1233.24,-2080.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1235.86,-2080.5 1233.24,-2073 1230.61,-2080.5 1235.86,-2080.5"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1166.55,-2120.3 1166.55,-2143.1 1233.24,-2143.1 1233.24,-2120.3 1166.55,-2120.3"/>
<text xml:space="preserve" text-anchor="start" x="1169.55" y="-2126.1" font-family="Arial" font-size="14.00" fill="#c9c9c9">normalize</text>
</g>
<!-- executeapi&#45;&gt;planvalidator -->
<g id="edge10" class="edge">
<title>executeapi&#45;&gt;planvalidator</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M680.16,-2160.09C680.16,-2160.09 680.16,-2080.5 680.16,-2080.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="682.79,-2080.5 680.16,-2073 677.54,-2080.5 682.79,-2080.5"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="502.92,-2120.3 502.92,-2143.1 680.16,-2143.1 680.16,-2120.3 502.92,-2120.3"/>
<text xml:space="preserve" text-anchor="start" x="505.92" y="-2126.1" font-family="Arial" font-size="14.00" fill="#c9c9c9">validate approved envelope</text>
</g>
<!-- corpusworker&#45;&gt;db -->
<g id="edge11" class="edge">
<title>corpusworker&#45;&gt;db</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M2249.95,-2220C2348.08,-2220 2446.3,-2220 2446.3,-2220 2446.3,-2220 2446.3,-2081.26 2446.3,-2081.26"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="2448.93,-2081.26 2446.3,-2073.76 2443.68,-2081.26 2448.93,-2081.26"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="2417.5,-2220 2417.5,-2242.8 2658.49,-2242.8 2658.49,-2220 2417.5,-2220"/>
<text xml:space="preserve" text-anchor="start" x="2420.5" y="-2225.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">inactive revision → validate → activate</text>
</g>
<!-- normalizer&#45;&gt;planner -->
<g id="edge12" class="edge">
<title>normalizer&#45;&gt;planner</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1389.06,-1890.09C1389.06,-1890.09 1389.06,-1810.5 1389.06,-1810.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1391.68,-1810.5 1389.06,-1803 1386.43,-1810.5 1391.68,-1810.5"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1289.68,-1850.3 1289.68,-1873.1 1389.06,-1873.1 1389.06,-1850.3 1289.68,-1850.3"/>
<text xml:space="preserve" text-anchor="start" x="1292.68" y="-1856.1" font-family="Arial" font-size="14.00" fill="#c9c9c9">questionFrame</text>
</g>
<!-- planvalidator&#45;&gt;lexical -->
<g id="edge13" class="edge">
<title>planvalidator&#45;&gt;lexical</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M659.1,-1890.09C659.1,-1890.09 659.1,-1810.5 659.1,-1810.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="661.72,-1810.5 659.1,-1803 656.47,-1810.5 661.72,-1810.5"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="474.88,-1850.3 474.88,-1873.1 659.1,-1873.1 659.1,-1850.3 474.88,-1850.3"/>
<text xml:space="preserve" text-anchor="start" x="477.88" y="-1856.1" font-family="Arial" font-size="14.00" fill="#c9c9c9">lexical route when requested</text>
</g>
<!-- planvalidator&#45;&gt;dense -->
<g id="edge14" class="edge">
<title>planvalidator&#45;&gt;dense</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M843.25,-1890.09C843.25,-1811.55 843.25,-1710 843.25,-1710 843.25,-1710 859.61,-1710 859.61,-1710"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="859.61,-1712.63 867.11,-1710 859.61,-1707.38 859.61,-1712.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="843.25,-1791.87 843.25,-1814.67 1026.71,-1814.67 1026.71,-1791.87 843.25,-1791.87"/>
<text xml:space="preserve" text-anchor="start" x="846.25" y="-1797.67" font-family="Arial" font-size="14.00" fill="#c9c9c9">dense route when requested</text>
</g>
<!-- planner&#45;&gt;spring -->
<g id="edge15" class="edge">
<title>planner&#45;&gt;spring</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1658.13,-1710C1737.37,-1710 1813.76,-1710 1813.76,-1710 1813.76,-1710 1813.76,-2419.69 1813.76,-2419.69"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1811.14,-2419.69 1813.76,-2427.19 1816.39,-2419.69 1811.14,-2419.69"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1724.49,-1987.03 1724.49,-2009.83 1813.76,-2009.83 1813.76,-1987.03 1724.49,-1987.03"/>
<text xml:space="preserve" text-anchor="start" x="1727.49" y="-1992.83" font-family="Arial" font-size="14.00" fill="#c9c9c9">PlanProposal</text>
</g>
<!-- lexical&#45;&gt;fusion -->
<g id="edge16" class="edge">
<title>lexical&#45;&gt;fusion</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M761.9,-1620.09C761.9,-1620.09 761.9,-1540.5 761.9,-1540.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="764.53,-1540.5 761.9,-1533 759.28,-1540.5 764.53,-1540.5"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="641.49,-1580.3 641.49,-1603.1 761.9,-1603.1 761.9,-1580.3 641.49,-1580.3"/>
<text xml:space="preserve" text-anchor="start" x="644.49" y="-1586.1" font-family="Arial" font-size="14.00" fill="#c9c9c9">ranked candidates</text>
</g>
<!-- dense&#45;&gt;fusion -->
<g id="edge17" class="edge">
<title>dense&#45;&gt;fusion</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M958.41,-1620.09C958.41,-1620.09 958.41,-1540.5 958.41,-1540.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="961.03,-1540.5 958.41,-1533 955.78,-1540.5 961.03,-1540.5"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="837.99,-1580.3 837.99,-1603.1 958.41,-1603.1 958.41,-1580.3 837.99,-1580.3"/>
<text xml:space="preserve" text-anchor="start" x="840.99" y="-1586.1" font-family="Arial" font-size="14.00" fill="#c9c9c9">ranked candidates</text>
</g>
<!-- fusion&#45;&gt;evidence -->
<g id="edge18" class="edge">
<title>fusion&#45;&gt;evidence</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M874.16,-1350.09C874.16,-1350.09 874.16,-1270.5 874.16,-1270.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="876.79,-1270.5 874.16,-1263 871.54,-1270.5 876.79,-1270.5"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="692.33,-1310.3 692.33,-1333.1 874.16,-1333.1 874.16,-1310.3 692.33,-1310.3"/>
<text xml:space="preserve" text-anchor="start" x="695.33" y="-1316.1" font-family="Arial" font-size="14.00" fill="#c9c9c9">RRF only for hybrid · rerank</text>
</g>
<!-- evidence&#45;&gt;prompt -->
<g id="edge19" class="edge">
<title>evidence&#45;&gt;prompt</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M874.16,-1080.09C874.16,-1080.09 874.16,-1000.5 874.16,-1000.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="876.79,-1000.5 874.16,-993 871.54,-1000.5 876.79,-1000.5"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="789.56,-1040.3 789.56,-1063.1 874.16,-1063.1 874.16,-1040.3 789.56,-1040.3"/>
<text xml:space="preserve" text-anchor="start" x="792.56" y="-1046.1" font-family="Arial" font-size="14.00" fill="#c9c9c9">EvidenceSet</text>
</g>
<!-- prompt&#45;&gt;generator -->
<g id="edge20" class="edge">
<title>prompt&#45;&gt;generator</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M874.16,-810.09C874.16,-810.09 874.16,-730.5 874.16,-730.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="876.79,-730.5 874.16,-723 871.54,-730.5 876.79,-730.5"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="766.2,-770.3 766.2,-793.1 874.16,-793.1 874.16,-770.3 766.2,-770.3"/>
<text xml:space="preserve" text-anchor="start" x="769.2" y="-776.1" font-family="Arial" font-size="14.00" fill="#c9c9c9">bounded prompt</text>
</g>
<!-- generator&#45;&gt;proposalvalidator -->
<g id="edge22" class="edge">
<title>generator&#45;&gt;proposalvalidator</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M874.16,-540.09C874.16,-540.09 874.16,-460.5 874.16,-460.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="876.79,-460.5 874.16,-453 871.54,-460.5 876.79,-460.5"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="738.61,-500.3 738.61,-523.1 874.16,-523.1 874.16,-500.3 738.61,-500.3"/>
<text xml:space="preserve" text-anchor="start" x="741.61" y="-506.1" font-family="Arial" font-size="14.00" fill="#c9c9c9">claim + evidence IDs</text>
</g>
<!-- generator&#45;&gt;gemini -->
<g id="edge21" class="edge">
<title>generator&#45;&gt;gemini</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M709.29,-660C492.12,-660 137.44,-660 137.44,-660 137.44,-660 137.44,-460.13 137.44,-460.13"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="140.07,-460.13 137.44,-452.63 134.82,-460.13 140.07,-460.13"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="191.35,-660 191.35,-682.8 323.43,-682.8 323.43,-660 191.35,-660"/>
<text xml:space="preserve" text-anchor="start" x="194.35" y="-665.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">public evidence only</text>
</g>
<!-- proposalvalidator&#45;&gt;spring -->
<g id="edge23" class="edge">
<title>proposalvalidator&#45;&gt;spring</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1065.11,-360C1340.82,-360 1817.74,-360 1817.74,-360 1817.74,-360 1817.74,-2419.75 1817.74,-2419.75"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1815.11,-2419.75 1817.74,-2427.25 1820.36,-2419.75 1815.11,-2419.75"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1698.1,-1013.56 1698.1,-1036.36 1817.74,-1036.36 1817.74,-1013.56 1698.1,-1013.56"/>
<text xml:space="preserve" text-anchor="start" x="1701.1" y="-1019.36" font-family="Arial" font-size="14.00" fill="#c9c9c9">ValidatedProposal</text>
</g>
<!-- proposalvalidator&#45;&gt;observability -->
<g id="edge24" class="edge">
<title>proposalvalidator&#45;&gt;observability</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M874.16,-230C874.16,-210.2 874.16,-190.5 874.16,-190.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="876.79,-190.5 874.16,-183 871.54,-190.5 876.79,-190.5"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="649.52,-210.25 649.52,-253.45 874.16,-253.45 874.16,-210.25 649.52,-210.25"/>
<text xml:space="preserve" text-anchor="start" x="652.52" y="-236.45" font-family="Arial" font-size="14.00" fill="#c9c9c9">child spans / retrieval stage metrics</text>
<text xml:space="preserve" text-anchor="start" x="652.52" y="-215.65" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ W3C trace context ]</text>
</g>
<!-- admin&#45;&gt;qualityharness -->
<g id="edge1" class="edge">
<title>admin&#45;&gt;qualityharness</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1316.7,-2550C1334.95,-2550 1346.47,-2550 1346.47,-2550 1346.47,-2550 1346.47,-2250 1346.47,-2250 1346.47,-2250 1366.2,-2250 1366.2,-2250"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1366.2,-2252.63 1373.7,-2250 1366.2,-2247.38 1366.2,-2252.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1142.03,-2365.43 1142.03,-2405.03 1346.47,-2405.03 1346.47,-2365.43 1142.03,-2365.43"/>
<text xml:space="preserve" text-anchor="start" x="1145.03" y="-2388.03" font-family="Arial" font-size="14.00" fill="#c9c9c9">operator&#45;selected investigation /</text>
<text xml:space="preserve" text-anchor="start" x="1145.03" y="-2371.23" font-family="Arial" font-size="14.00" fill="#c9c9c9">experiment</text>
</g>
<!-- gemini&#45;&gt;generator -->
<g id="edge2" class="edge">
<title>gemini&#45;&gt;generator</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M274.88,-449.71C274.88,-517.88 274.88,-600 274.88,-600 274.88,-600 698.69,-600 698.69,-600"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="698.69,-602.63 706.19,-600 698.69,-597.38 698.69,-602.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="285.8,-600 285.8,-622.8 411.64,-622.8 411.64,-600 285.8,-600"/>
<text xml:space="preserve" text-anchor="start" x="288.8" y="-605.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">structured proposal</text>
</g>
<!-- spring&#45;&gt;qualityharness -->
<g id="edge3" class="edge">
<title>spring&#45;&gt;qualityharness</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1593.16,-2430.09C1593.16,-2430.09 1593.16,-2350.5 1593.16,-2350.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1595.79,-2350.5 1593.16,-2343 1590.54,-2350.5 1595.79,-2350.5"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1411.3,-2390.3 1411.3,-2413.1 1593.16,-2413.1 1593.16,-2390.3 1411.3,-2390.3"/>
<text xml:space="preserve" text-anchor="start" x="1414.3" y="-2396.1" font-family="Arial" font-size="14.00" fill="#c9c9c9">privacy&#45;safe run observation</text>
</g>
<!-- spring&#45;&gt;planapi -->
<g id="edge4" class="edge">
<title>spring&#45;&gt;planapi</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1364.9,-2490C1339.54,-2490 1322.64,-2490 1322.64,-2490 1322.64,-2490 1322.64,-2350.24 1322.64,-2350.24"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1325.26,-2350.24 1322.64,-2342.74 1320.01,-2350.24 1325.26,-2350.24"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1212.24,-2418.45 1212.24,-2441.25 1433.03,-2441.25 1433.03,-2418.45 1212.24,-2418.45"/>
<text xml:space="preserve" text-anchor="start" x="1215.24" y="-2424.25" font-family="Arial" font-size="14.00" fill="#c9c9c9">plan request · transient safeQuery</text>
</g>
<!-- spring&#45;&gt;executeapi -->
<g id="edge5" class="edge">
<title>spring&#45;&gt;executeapi</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1370.58,-2430.33C1370.58,-2405.39 1370.58,-2385 1370.58,-2385 1370.58,-2385 855.65,-2385 855.65,-2385 855.65,-2385 855.65,-2350.2 855.65,-2350.2"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="858.28,-2350.2 855.66,-2342.7 853.03,-2350.2 858.28,-2350.2"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="948.93,-2385 948.93,-2407.8 1118.38,-2407.8 1118.38,-2385 948.93,-2385"/>
<text xml:space="preserve" text-anchor="start" x="951.93" y="-2390.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">approved plan · planHash</text>
</g>
<!-- db&#45;&gt;qualityharness -->
<g id="edge6" class="edge">
<title>db&#45;&gt;qualityharness</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M2329.63,-1950C2095.52,-1950 1708.86,-1950 1708.86,-1950 1708.86,-1950 1708.86,-2149.87 1708.86,-2149.87"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1706.24,-2149.87 1708.86,-2157.37 1711.49,-2149.87 1706.24,-2149.87"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1731.57,-1950 1731.57,-1972.8 1919.31,-1972.8 1919.31,-1950 1731.57,-1950"/>
<text xml:space="preserve" text-anchor="start" x="1734.57" y="-1955.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">gold set + expected evidence</text>
</g>
<!-- db&#45;&gt;corpusworker -->
<g id="edge7" class="edge">
<title>db&#45;&gt;corpusworker</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M2562.02,-2070.82C2562.02,-2159.12 2562.02,-2280 2562.02,-2280 2562.02,-2280 2260.68,-2280 2260.68,-2280"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="2260.68,-2277.38 2253.18,-2280 2260.68,-2282.63 2260.68,-2277.38"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="2306.44,-2280 2306.44,-2302.8 2515.94,-2302.8 2515.94,-2280 2306.44,-2280"/>
<text xml:space="preserve" text-anchor="start" x="2309.44" y="-2285.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">public projection + rights revision</text>
</g>
</g>
</svg>
`;case`production-deployment`:return`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Generated by graphviz version 16.1.0 (0)
 -->
<!-- Pages: 1 -->
<svg width="2163pt" height="1139pt"
 viewBox="0.00 0.00 2163.00 1139.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(15.05 1123.85)">
<g id="clust1" class="cluster">
<title>cluster_aws</title>
<polygon fill="#1a468d" stroke="#1c3979" points="8,-8 8,-1100.8 1295,-1100.8 1295,-8 8,-8"/>
<text xml:space="preserve" text-anchor="start" x="16" y="-1087.9" font-family="Arial" font-weight="bold" font-size="11.00" fill="#bfdbfe" fill-opacity="0.701961">AWS</text>
</g>
<g id="clust2" class="cluster">
<title>cluster_lightsail2gb</title>
<polygon fill="#194b9e" stroke="#1b3d88" points="40,-40 40,-1047.6 1263,-1047.6 1263,-40 40,-40"/>
<text xml:space="preserve" text-anchor="start" x="48" y="-1034.7" font-family="Arial" font-weight="bold" font-size="11.00" fill="#bfdbfe" fill-opacity="0.701961">LIGHTSAIL2GB</text>
</g>
<!-- springinstance -->
<g id="node1" class="node">
<title>springinstance</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="547.54,-976.4 90.46,-976.4 90.46,-796.4 547.54,-796.4 547.54,-976.4"/>
<text xml:space="preserve" text-anchor="start" x="238.97" y="-899.2" font-family="Arial" font-size="20.00" fill="#eff6ff">Spring API Server</text>
<text xml:space="preserve" text-anchor="start" x="130.46" y="-878.2" font-family="Arial" font-size="13.00" fill="#bfdbfe">회원 인증·대화·쿼리 권한·정형 SQL·최종 검증·영속화·SSE를 소유한다.</text>
<text xml:space="preserve" text-anchor="start" x="231.88" y="-856.6" font-family="Arial" font-size="15.00" fill="#bfdbfe">Spring Boot · 독립 프로세스</text>
</g>
<!-- geminiinstance -->
<g id="node2" class="node">
<title>geminiinstance</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1885.16,-976.4 1472.84,-976.4 1472.84,-796.4 1885.16,-796.4 1885.16,-976.4"/>
<text xml:space="preserve" text-anchor="start" x="1628.43" y="-899.2" font-family="Arial" font-size="20.00" fill="#eff6ff">Gemini API</text>
<text xml:space="preserve" text-anchor="start" x="1512.84" y="-878.2" font-family="Arial" font-size="13.00" fill="#bfdbfe">공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을</text>
<text xml:space="preserve" text-anchor="start" x="1645.65" y="-856.6" font-family="Arial" font-size="15.00" fill="#bfdbfe">Google AI</text>
</g>
<!-- webinstance -->
<g id="node3" class="node">
<title>webinstance</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1647.02,-623.2 1326.98,-623.2 1326.98,-443.2 1647.02,-443.2 1647.02,-623.2"/>
<text xml:space="preserve" text-anchor="start" x="1433.1" y="-546" font-family="Arial" font-size="20.00" fill="#eff6ff">Next.js Web</text>
<text xml:space="preserve" text-anchor="start" x="1357.33" y="-525" font-family="Arial" font-size="13.00" fill="#bfdbfe">대화 입력, SSE 표시, 장소 카드, 출처, 이어하기 UI.</text>
<text xml:space="preserve" text-anchor="start" x="1434.49" y="-503.4" font-family="Arial" font-size="15.00" fill="#bfdbfe">Next.js · Vercel</text>
</g>
<!-- nginxinstance -->
<g id="node4" class="node">
<title>nginxinstance</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="961.34,-270 544.66,-270 544.66,-90 961.34,-90 961.34,-270"/>
<text xml:space="preserve" text-anchor="start" x="671.3" y="-192.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Public API Ingress</text>
<text xml:space="preserve" text-anchor="start" x="584.66" y="-171.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">외부에 80/443만 열고 HTTPS와 SSE를 Spring API로 전달한다.</text>
<text xml:space="preserve" text-anchor="start" x="697.97" y="-150.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Nginx · Lightsail</text>
</g>
<!-- aiinstance -->
<g id="node5" class="node">
<title>aiinstance</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1212.91,-976.4 807.09,-976.4 807.09,-796.4 1212.91,-796.4 1212.91,-976.4"/>
<text xml:space="preserve" text-anchor="start" x="929.98" y="-899.2" font-family="Arial" font-size="20.00" fill="#eff6ff">FastAPI AI Server</text>
<text xml:space="preserve" text-anchor="start" x="847.09" y="-878.2" font-family="Arial" font-size="13.00" fill="#bfdbfe">비공개 AI API. 질문 해석·route 제안·승인 plan 검색·근거 제한</text>
<text xml:space="preserve" text-anchor="start" x="850.77" y="-856.6" font-family="Arial" font-size="15.00" fill="#bfdbfe">Python · 독립 프로세스 · onmaru&#45;ai&#45;engine 저장소</text>
</g>
<!-- grafanainstance -->
<g id="node6" class="node">
<title>grafanainstance</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="2133.35,-623.2 1776.65,-623.2 1776.65,-443.2 2133.35,-443.2 2133.35,-623.2"/>
<text xml:space="preserve" text-anchor="start" x="1889.96" y="-546" font-family="Arial" font-size="20.00" fill="#eff6ff">Grafana Cloud</text>
<text xml:space="preserve" text-anchor="start" x="1816.65" y="-525" font-family="Arial" font-size="13.00" fill="#bfdbfe">공통 trace 조회, metric/dashboard/alerts, 품질 검토</text>
<text xml:space="preserve" text-anchor="start" x="1853.71" y="-503.4" font-family="Arial" font-size="15.00" fill="#bfdbfe">OTel / Prometheus compatible</text>
</g>
<!-- dbinstance -->
<g id="node7" class="node">
<title>dbinstance</title>
<path fill="#3b82f6" stroke="#2563eb" stroke-width="2" d="M492.57,-606.84C492.57,-615.87 414.78,-623.2 319,-623.2 223.22,-623.2 145.43,-615.87 145.43,-606.84 145.43,-606.84 145.43,-459.56 145.43,-459.56 145.43,-450.53 223.22,-443.2 319,-443.2 414.78,-443.2 492.57,-450.53 492.57,-459.56 492.57,-459.56 492.57,-606.84 492.57,-606.84"/>
<path fill="none" stroke="#2563eb" stroke-width="2" d="M492.57,-606.84C492.57,-597.81 414.78,-590.47 319,-590.47 223.22,-590.47 145.43,-597.81 145.43,-606.84"/>
<text xml:space="preserve" text-anchor="start" x="264.53" y="-546" font-family="Arial" font-size="20.00" fill="#eff6ff">PostgreSQL</text>
<text xml:space="preserve" text-anchor="start" x="165.48" y="-525" font-family="Arial" font-size="13.00" fill="#bfdbfe">업무 schema와 ai schema를 논리·role 권한으로 분리한다.</text>
<text xml:space="preserve" text-anchor="start" x="194.77" y="-503.4" font-family="Arial" font-size="15.00" fill="#bfdbfe">PostGIS + pgvector + Korean full&#45;text</text>
</g>
<!-- springinstance&#45;&gt;webinstance -->
<g id="edge2" class="edge">
<title>springinstance&#45;&gt;webinstance</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M547.24,-835.8C747.25,-789.58 1044.32,-714.21 1295,-623.2 1302.41,-620.51 1309.92,-617.65 1317.47,-614.66"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1318.26,-617.17 1324.24,-611.94 1316.3,-612.3 1318.26,-617.17"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1085.05,-688.2 1085.05,-731.4 1215.09,-731.4 1215.09,-688.2 1085.05,-688.2"/>
<text xml:space="preserve" text-anchor="start" x="1088.05" y="-716.8" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">[...]</text>
<text xml:space="preserve" text-anchor="start" x="1088.05" y="-693.6" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ SSE · Last&#45;Event&#45;ID ]</text>
</g>
<!-- springinstance&#45;&gt;aiinstance -->
<g id="edge7" class="edge">
<title>springinstance&#45;&gt;aiinstance</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M557.57,-886.4C635.44,-886.4 721.35,-886.4 797.2,-886.4"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="557.7,-883.78 550.2,-886.4 557.7,-889.03 557.7,-883.78"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="796.83,-889.03 804.33,-886.4 796.83,-883.78 796.83,-889.03"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="663.82,-889.4 663.82,-912.2 690.81,-912.2 690.81,-889.4 663.82,-889.4"/>
<text xml:space="preserve" text-anchor="start" x="666.82" y="-897.6" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">[...]</text>
</g>
<!-- springinstance&#45;&gt;grafanainstance -->
<g id="edge4" class="edge">
<title>springinstance&#45;&gt;grafanainstance</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M547.5,-833.86C610.35,-820.63 678.64,-807.13 742,-796.4 965.12,-758.63 1024.29,-771.54 1247,-731.4 1455.82,-693.76 1508.66,-683.85 1712,-623.2 1729.88,-617.87 1748.36,-611.92 1766.77,-605.7"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1767.56,-608.2 1773.81,-603.3 1765.87,-603.23 1767.56,-608.2"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1465.99,-688.2 1465.99,-731.4 1679.73,-731.4 1679.73,-688.2 1465.99,-688.2"/>
<text xml:space="preserve" text-anchor="start" x="1468.99" y="-714.4" font-family="Arial" font-size="14.00" fill="#c9c9c9">root span / low&#45;cardinality metrics</text>
<text xml:space="preserve" text-anchor="start" x="1468.99" y="-693.6" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ OTLP ]</text>
</g>
<!-- springinstance&#45;&gt;dbinstance -->
<g id="edge8" class="edge">
<title>springinstance&#45;&gt;dbinstance</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M319,-796.78C319,-747.35 319,-685.62 319,-634.44"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="321.63,-634.54 319,-627.04 316.38,-634.54 321.63,-634.54"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="319,-688.2 319,-731.4 416.37,-731.4 416.37,-688.2 319,-688.2"/>
<text xml:space="preserve" text-anchor="start" x="322" y="-716.8" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">[...]</text>
<text xml:space="preserve" text-anchor="start" x="322" y="-693.6" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ Spring DB role ]</text>
</g>
<!-- geminiinstance&#45;&gt;aiinstance -->
<g id="edge3" class="edge">
<title>geminiinstance&#45;&gt;aiinstance</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1462.8,-886.4C1385.88,-886.4 1299.38,-886.4 1222.75,-886.4"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1462.58,-889.03 1470.08,-886.4 1462.58,-883.78 1462.58,-889.03"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1223.06,-883.78 1215.56,-886.4 1223.06,-889.03 1223.06,-883.78"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1313.54,-889.4 1313.54,-932.6 1372.21,-932.6 1372.21,-889.4 1313.54,-889.4"/>
<text xml:space="preserve" text-anchor="start" x="1316.54" y="-918" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">[...]</text>
<text xml:space="preserve" text-anchor="start" x="1316.54" y="-894.8" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ HTTPS ]</text>
</g>
<!-- webinstance&#45;&gt;nginxinstance -->
<g id="edge1" class="edge">
<title>webinstance&#45;&gt;nginxinstance</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1357.39,-443.27C1301.26,-406.97 1233.89,-366.27 1170,-335 1106.9,-304.12 1035.96,-275.73 970.72,-251.96"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="971.93,-249.61 963.99,-249.52 970.14,-254.55 971.93,-249.61"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1242.22,-335 1242.22,-378.2 1432.67,-378.2 1432.67,-335 1242.22,-335"/>
<text xml:space="preserve" text-anchor="start" x="1245.22" y="-361.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">API request / SSE connection</text>
<text xml:space="preserve" text-anchor="start" x="1245.22" y="-340.4" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ HTTPS · api.onmaru.site ]</text>
</g>
<!-- nginxinstance&#45;&gt;springinstance -->
<g id="edge6" class="edge">
<title>nginxinstance&#45;&gt;springinstance</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M723.59,-269.58C690.74,-362.02 632.29,-509.12 558,-623.2 519.16,-682.85 466.68,-742.08 420.79,-789.11"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="418.98,-787.2 415.6,-794.39 422.73,-790.88 418.98,-787.2"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="651.81,-511.6 651.81,-554.8 876.49,-554.8 876.49,-511.6 651.81,-511.6"/>
<text xml:space="preserve" text-anchor="start" x="654.81" y="-537.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">proxy API / SSE; buffering disabled</text>
<text xml:space="preserve" text-anchor="start" x="654.81" y="-517" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ private Docker network ]</text>
</g>
<!-- aiinstance&#45;&gt;grafanainstance -->
<g id="edge5" class="edge">
<title>aiinstance&#45;&gt;grafanainstance</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1212.76,-837.65C1275.22,-823.6 1344.3,-808.7 1408,-796.4 1584.41,-762.34 1653.29,-824.43 1807,-731.4 1846.5,-707.5 1878.98,-668.73 1903.36,-631.87"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1905.55,-633.32 1907.42,-625.59 1901.14,-630.47 1905.55,-633.32"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1858.39,-688.2 1858.39,-731.4 2083.03,-731.4 2083.03,-688.2 1858.39,-688.2"/>
<text xml:space="preserve" text-anchor="start" x="1861.39" y="-714.4" font-family="Arial" font-size="14.00" fill="#c9c9c9">child spans / retrieval stage metrics</text>
<text xml:space="preserve" text-anchor="start" x="1861.39" y="-693.6" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ W3C trace context ]</text>
</g>
<!-- aiinstance&#45;&gt;dbinstance -->
<g id="edge9" class="edge">
<title>aiinstance&#45;&gt;dbinstance</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M825.93,-791.85C722.48,-739.27 594.1,-674.02 492.43,-622.34"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="824.61,-794.12 832.49,-795.18 826.99,-789.44 824.61,-794.12"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="493.87,-620.13 486,-619.08 491.49,-624.81 493.87,-620.13"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="705.87,-688.2 705.87,-731.4 857.26,-731.4 857.26,-688.2 705.87,-688.2"/>
<text xml:space="preserve" text-anchor="start" x="708.87" y="-716.8" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">[...]</text>
<text xml:space="preserve" text-anchor="start" x="708.87" y="-693.6" font-family="Arial" font-size="12.00" fill="#c9c9c9">[ AI least&#45;privilege DB role ]</text>
</g>
</g>
</svg>
`;case`online-rag-sse`:return`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Generated by graphviz version 16.1.0 (0)
 -->
<!-- Pages: 1 -->
<svg width="8513pt" height="1030pt"
 viewBox="0.00 0.00 8513.00 1030.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(15.05 1015.05)">
<g id="clust1" class="cluster">
<title>cluster_onmaru</title>
<polygon fill="#194b9e" stroke="#1b3d88" points="8,-131 8,-992 7748.57,-992 7748.57,-131 8,-131"/>
<text xml:space="preserve" text-anchor="start" x="16" y="-979.1" font-family="Arial" font-weight="bold" font-size="11.00" fill="#bfdbfe" fill-opacity="0.701961">ONMARU</text>
</g>
<!-- web -->
<g id="node1" class="node">
<title>web</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="368.04,-832 48,-832 48,-652 368.04,-652 368.04,-832"/>
<text xml:space="preserve" text-anchor="start" x="154.12" y="-754.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Next.js Web</text>
<text xml:space="preserve" text-anchor="start" x="78.35" y="-733.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">대화 입력, SSE 표시, 장소 카드, 출처, 이어하기 UI.</text>
<text xml:space="preserve" text-anchor="start" x="155.51" y="-712.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Next.js · Vercel</text>
</g>
<!-- nginx -->
<g id="node2" class="node">
<title>nginx</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1147.2,-844 730.53,-844 730.53,-664 1147.2,-664 1147.2,-844"/>
<text xml:space="preserve" text-anchor="start" x="857.16" y="-766.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Public API Ingress</text>
<text xml:space="preserve" text-anchor="start" x="770.53" y="-745.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">외부에 80/443만 열고 HTTPS와 SSE를 Spring API로 전달한다.</text>
<text xml:space="preserve" text-anchor="start" x="883.84" y="-724.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Nginx · Lightsail</text>
</g>
<!-- admission -->
<g id="node3" class="node">
<title>admission</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1898.01,-931 1567.96,-931 1567.96,-751 1898.01,-751 1898.01,-931"/>
<text xml:space="preserve" text-anchor="start" x="1615.71" y="-853.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Admission &amp; Conversation</text>
<text xml:space="preserve" text-anchor="start" x="1624.63" y="-832.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">소유권, 사용량, 대화 컨텍스트, 멱등성 검사.</text>
<text xml:space="preserve" text-anchor="start" x="1678.79" y="-811.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">auth / run / state</text>
</g>
<!-- privacy -->
<g id="node4" class="node">
<title>privacy</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="2655.06,-931 2325.02,-931 2325.02,-751 2655.06,-751 2655.06,-931"/>
<text xml:space="preserve" text-anchor="start" x="2407.78" y="-853.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Input Privacy Gate</text>
<text xml:space="preserve" text-anchor="start" x="2366.87" y="-832.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">원문을 유지하고 AI plan용 비식별 질문을 만든다.</text>
<text xml:space="preserve" text-anchor="start" x="2455.44" y="-811.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">safeQuery</text>
</g>
<!-- authority -->
<g id="node5" class="node">
<title>authority</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="2664.41,-616 2315.67,-616 2315.67,-436 2664.41,-436 2664.41,-616"/>
<text xml:space="preserve" text-anchor="start" x="2403.33" y="-538.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Plan Authority Gate</text>
<text xml:space="preserve" text-anchor="start" x="2355.67" y="-517.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">route·정형 필드·ID·공개 필터·version을 승인한다.</text>
<text xml:space="preserve" text-anchor="start" x="2422.52" y="-496.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">allowlist / hard filters</text>
</g>
<!-- planapi -->
<g id="node6" class="node">
<title>planapi</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="3466.09,-931 3053.75,-931 3053.75,-751 3466.09,-751 3466.09,-931"/>
<text xml:space="preserve" text-anchor="start" x="3221.01" y="-853.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Plan API</text>
<text xml:space="preserve" text-anchor="start" x="3093.75" y="-832.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">safeQuery와 구조화 맥락을 해석하고 PlanProposal을 반환한다.</text>
<text xml:space="preserve" text-anchor="start" x="3180.72" y="-811.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">POST /internal/v1/plans</text>
</g>
<!-- normalizer -->
<g id="node7" class="node">
<title>normalizer</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="4193.71,-931 3863.66,-931 3863.66,-751 4193.71,-751 4193.71,-931"/>
<text xml:space="preserve" text-anchor="start" x="3950.34" y="-853.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Query Normalizer</text>
<text xml:space="preserve" text-anchor="start" x="3911.3" y="-832.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">동의어·주제·대상·부정·다턴 맥락을 보존한다.</text>
<text xml:space="preserve" text-anchor="start" x="3952.4" y="-811.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">alias / polarity / context</text>
</g>
<!-- planner -->
<g id="node8" class="node">
<title>planner</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="4995.64,-931 4647.17,-931 4647.17,-751 4995.64,-751 4995.64,-931"/>
<text xml:space="preserve" text-anchor="start" x="4714.68" y="-853.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Query Planner &amp; Router</text>
<text xml:space="preserve" text-anchor="start" x="4727.13" y="-832.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">결정적 route와 조회 제약을 제안한다.</text>
<text xml:space="preserve" text-anchor="start" x="4687.17" y="-811.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">SQL / lexical / dense / hybrid / combined</text>
</g>
<!-- sqlexecutor -->
<g id="node9" class="node">
<title>sqlexecutor</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="3424.95,-351 3094.9,-351 3094.9,-171 3424.95,-171 3424.95,-351"/>
<text xml:space="preserve" text-anchor="start" x="3150.42" y="-273.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Canonical SQL Executor</text>
<text xml:space="preserve" text-anchor="start" x="3139.64" y="-252.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">허용된 정형 사실만 업무 schema에서 조회한다.</text>
<text xml:space="preserve" text-anchor="start" x="3194.89" y="-231.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">parameterized SQL</text>
</g>
<!-- businessschema -->
<g id="node10" class="node">
<title>businessschema</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="4193.71,-351 3863.66,-351 3863.66,-171 4193.71,-171 4193.71,-351"/>
<text xml:space="preserve" text-anchor="start" x="3948.65" y="-273.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Business Schema</text>
<text xml:space="preserve" text-anchor="start" x="3923.56" y="-252.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">회원·대화·장소·권리의 canonical data.</text>
<text xml:space="preserve" text-anchor="start" x="3982.41" y="-231.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Spring&#45;owned</text>
</g>
<!-- executeapi -->
<g id="node11" class="node">
<title>executeapi</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="3447.68,-641 3072.16,-641 3072.16,-461 3447.68,-461 3447.68,-641"/>
<text xml:space="preserve" text-anchor="start" x="3204.89" y="-563.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Execute API</text>
<text xml:space="preserve" text-anchor="start" x="3112.16" y="-542.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">Spring이 승인한 plan hash와 필요한 CanonicalFacts만</text>
<text xml:space="preserve" text-anchor="start" x="3142.78" y="-521.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">POST /internal/v1/runs/{id}/execute</text>
</g>
<!-- planvalidator -->
<g id="node12" class="node">
<title>planvalidator</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="4212.84,-641 3844.53,-641 3844.53,-461 4212.84,-461 4212.84,-641"/>
<text xml:space="preserve" text-anchor="start" x="3920.84" y="-563.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Approved Plan Validator</text>
<text xml:space="preserve" text-anchor="start" x="3884.53" y="-542.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">승인 plan·config·corpus·철회 sequence를 검증한다.</text>
<text xml:space="preserve" text-anchor="start" x="3954.9" y="-521.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">hash / revision / policy</text>
</g>
<!-- lexical -->
<g id="node13" class="node">
<title>lexical</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="4986.43,-641 4656.38,-641 4656.38,-461 4986.43,-461 4986.43,-641"/>
<text xml:space="preserve" text-anchor="start" x="4746.93" y="-563.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Lexical Retriever</text>
<text xml:space="preserve" text-anchor="start" x="4716.66" y="-542.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">한국어 토큰 검색 후보와 rank를 반환한다.</text>
<text xml:space="preserve" text-anchor="start" x="4755.96" y="-521.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">exact / alias / BM25</text>
</g>
<!-- dense -->
<g id="node14" class="node">
<title>dense</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="5017.47,-351 4625.34,-351 4625.34,-171 5017.47,-171 5017.47,-351"/>
<text xml:space="preserve" text-anchor="start" x="4749.15" y="-273.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Dense Retriever</text>
<text xml:space="preserve" text-anchor="start" x="4665.34" y="-252.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">같은 embedding profile의 query vector로 후보를 반환한다.</text>
<text xml:space="preserve" text-anchor="start" x="4738.03" y="-231.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">e5&#45;small 384D / pgvector</text>
</g>
<!-- fusion -->
<g id="node15" class="node">
<title>fusion</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="5679.33,-371 5334.23,-371 5334.23,-191 5679.33,-191 5679.33,-371"/>
<text xml:space="preserve" text-anchor="start" x="5432.3" y="-293.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Fusion &amp; Ranker</text>
<text xml:space="preserve" text-anchor="start" x="5374.23" y="-272.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">두 검색기일 때 RRF, 이후 후보 재순위화를 수행한다.</text>
<text xml:space="preserve" text-anchor="start" x="5419.24" y="-251.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">conditional RRF / reranker</text>
</g>
<!-- evidence -->
<g id="node16" class="node">
<title>evidence</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="6418.71,-371 6088.66,-371 6088.66,-191 6418.71,-191 6418.71,-371"/>
<text xml:space="preserve" text-anchor="start" x="6173.08" y="-293.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Evidence Selector</text>
<text xml:space="preserve" text-anchor="start" x="6143.15" y="-272.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">장소별 출처·revision·본문 span을 고른다.</text>
<text xml:space="preserve" text-anchor="start" x="6203.24" y="-251.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">max 12 chunks</text>
</g>
<!-- prompt -->
<g id="node17" class="node">
<title>prompt</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="7109.99,-371 6762.71,-371 6762.71,-191 7109.99,-191 7109.99,-371"/>
<text xml:space="preserve" text-anchor="start" x="6854.1" y="-293.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Prompt Assembler</text>
<text xml:space="preserve" text-anchor="start" x="6802.71" y="-272.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">추천·수정·해설·비교 템플릿과 공개 근거만 구성한다.</text>
<text xml:space="preserve" text-anchor="start" x="6887.99" y="-251.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">task templates</text>
</g>
<!-- generator -->
<g id="node18" class="node">
<title>generator</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="7708.57,-361 7378.52,-361 7378.52,-181 7708.57,-181 7708.57,-361"/>
<text xml:space="preserve" text-anchor="start" x="7451.27" y="-283.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Grounded Generator</text>
<text xml:space="preserve" text-anchor="start" x="7454.34" y="-262.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">근거 기반 구조화 claim을 제안한다.</text>
<text xml:space="preserve" text-anchor="start" x="7463.09" y="-241.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Gemini provider adapter</text>
</g>
<!-- finalvalidator -->
<g id="node19" class="node">
<title>finalvalidator</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1103.89,-447 773.84,-447 773.84,-267 1103.89,-267 1103.89,-447"/>
<text xml:space="preserve" text-anchor="start" x="874.94" y="-369.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Final Validator</text>
<text xml:space="preserve" text-anchor="start" x="822.56" y="-348.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">장소·출처·철회·조건·claim을 다시 검증한다.</text>
<text xml:space="preserve" text-anchor="start" x="874.26" y="-327.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">claim / rights / state</text>
</g>
<!-- proposalvalidator -->
<g id="node20" class="node">
<title>proposalvalidator</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1923.97,-351 1542,-351 1542,-171 1923.97,-171 1923.97,-351"/>
<text xml:space="preserve" text-anchor="start" x="1651.27" y="-273.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Proposal Validator</text>
<text xml:space="preserve" text-anchor="start" x="1582" y="-252.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">claim별 evidence ID·장소 ID·길이·schema를 검증한다.</text>
<text xml:space="preserve" text-anchor="start" x="1618.35" y="-231.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">closed schema / evidence allowlist</text>
</g>
<!-- gemini -->
<g id="node21" class="node">
<title>gemini</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="8482.83,-180 8070.5,-180 8070.5,0 8482.83,0 8482.83,-180"/>
<text xml:space="preserve" text-anchor="start" x="8226.09" y="-102.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Gemini API</text>
<text xml:space="preserve" text-anchor="start" x="8110.5" y="-81.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">공개 근거와 허용된 주제 code만 받고 구조화된 claim proposal을</text>
<text xml:space="preserve" text-anchor="start" x="8243.31" y="-60.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Google AI</text>
</g>
<!-- persistence -->
<g id="node22" class="node">
<title>persistence</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1921.44,-641 1544.54,-641 1544.54,-461 1921.44,-461 1921.44,-641"/>
<text xml:space="preserve" text-anchor="start" x="1627.38" y="-563.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Run Persistence &amp; SSE</text>
<text xml:space="preserve" text-anchor="start" x="1584.54" y="-542.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">확정 답변을 저장한 뒤 상태와 답변 조각을 SSE로 전송한다.</text>
<text xml:space="preserve" text-anchor="start" x="1675.87" y="-521.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">snapshot / replay</text>
</g>
<!-- web&#45;&gt;nginx -->
<g id="edge1" class="edge">
<title>web&#45;&gt;nginx</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M368,-658.71C387.79,-651.21 408.09,-644.8 428.04,-640.4 533.28,-617.18 564.92,-618.89 670.53,-640.4 694.41,-645.26 718.81,-652.34 742.67,-660.62"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="741.71,-663.07 749.65,-663.1 743.46,-658.12 741.71,-663.07"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="431.04,-643.4 431.04,-683 455.04,-683 455.04,-643.4 431.04,-643.4"/>
<text xml:space="preserve" text-anchor="start" x="439.15" y="-660" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">0</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="458.04,-643.4 458.04,-683 667.53,-683 667.53,-643.4 458.04,-643.4"/>
<text xml:space="preserve" text-anchor="start" x="461.04" y="-666" font-family="Arial" font-size="14.00" fill="#c9c9c9">HTTPS · create run + open SSE</text>
<text xml:space="preserve" text-anchor="start" x="484.2" y="-649.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">HTTPS · api.onmaru.site</text>
</g>
<!-- web&#45;&gt;nginx -->
<g id="edge24" class="edge">
<title>web&#45;&gt;nginx</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M378.02,-744.78C483.17,-746.51 619.15,-748.75 730.76,-750.59"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="378.19,-742.16 370.64,-744.66 378.1,-747.41 378.19,-742.16"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="457.03,-752.43 457.03,-785.23 488.6,-785.23 488.6,-752.43 457.03,-752.43"/>
<text xml:space="preserve" text-anchor="start" x="465.03" y="-765.63" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">23</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="491.6,-752.43 491.6,-785.23 641.54,-785.23 641.54,-752.43 491.6,-752.43"/>
<text xml:space="preserve" text-anchor="start" x="494.6" y="-763.23" font-family="Arial" font-size="14.00" fill="#c9c9c9">SSE stream to browser</text>
</g>
<!-- nginx&#45;&gt;admission -->
<g id="edge2" class="edge">
<title>nginx&#45;&gt;admission</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1146.95,-776.74C1274.8,-790.79 1436.97,-808.6 1558.12,-821.9"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1557.49,-824.48 1565.23,-822.69 1558.06,-819.26 1557.49,-824.48"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1210.2,-815.86 1210.2,-848.66 1234.2,-848.66 1234.2,-815.86 1210.2,-815.86"/>
<text xml:space="preserve" text-anchor="start" x="1218.31" y="-829.06" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">1</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1237.2,-815.86 1237.2,-848.66 1479,-848.66 1479,-815.86 1237.2,-815.86"/>
<text xml:space="preserve" text-anchor="start" x="1240.2" y="-826.66" font-family="Arial" font-size="14.00" fill="#c9c9c9">POST /api/v1/journeys/{threadId}/runs</text>
</g>
<!-- nginx&#45;&gt;persistence -->
<g id="edge23" class="edge">
<title>nginx&#45;&gt;persistence</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1157.12,-698.32C1278.6,-667.19 1428.47,-628.78 1544.72,-598.99"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1156.49,-695.77 1149.88,-700.18 1157.8,-700.86 1156.49,-695.77"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1238.33,-685.54 1238.33,-718.34 1269.9,-718.34 1269.9,-685.54 1238.33,-685.54"/>
<text xml:space="preserve" text-anchor="start" x="1246.33" y="-698.74" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">22</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1272.9,-685.54 1272.9,-718.34 1450.87,-718.34 1450.87,-685.54 1272.9,-685.54"/>
<text xml:space="preserve" text-anchor="start" x="1275.9" y="-696.34" font-family="Arial" font-size="14.00" fill="#c9c9c9">verified SSE events / replay</text>
</g>
<!-- admission&#45;&gt;privacy -->
<g id="edge3" class="edge">
<title>admission&#45;&gt;privacy</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1897.82,-841C2020.9,-841 2189.16,-841 2314.71,-841"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="2314.67,-843.63 2322.17,-841 2314.67,-838.38 2314.67,-843.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1986.97,-844 1986.97,-876.8 2010.97,-876.8 2010.97,-844 1986.97,-844"/>
<text xml:space="preserve" text-anchor="start" x="1995.08" y="-857.2" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">2</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="2013.97,-844 2013.97,-876.8 2252.67,-876.8 2252.67,-844 2013.97,-844"/>
<text xml:space="preserve" text-anchor="start" x="2016.97" y="-854.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">authenticate · load confirmed context</text>
</g>
<!-- privacy&#45;&gt;planapi -->
<g id="edge4" class="edge">
<title>privacy&#45;&gt;planapi</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M2654.83,-841C2768.25,-841 2920.4,-841 3043.62,-841"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="3043.41,-843.63 3050.91,-841 3043.41,-838.38 3043.41,-843.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="2728.59,-844 2728.59,-876.8 2752.59,-876.8 2752.59,-844 2728.59,-844"/>
<text xml:space="preserve" text-anchor="start" x="2736.69" y="-857.2" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">3</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="2755.59,-844 2755.59,-876.8 2989.58,-876.8 2989.58,-844 2755.59,-844"/>
<text xml:space="preserve" text-anchor="start" x="2758.59" y="-854.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">POST /internal/v1/plans · safeQuery</text>
</g>
<!-- authority&#45;&gt;planapi -->
<g id="edge7" class="edge">
<title>authority&#45;&gt;planapi</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M2673.89,-601.01C2788.2,-647.9 2935.65,-708.39 3053.92,-756.9"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="2675.06,-598.65 2667.13,-598.23 2673.07,-603.51 2675.06,-598.65"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="2800.94,-733.12 2800.94,-765.92 2824.94,-765.92 2824.94,-733.12 2800.94,-733.12"/>
<text xml:space="preserve" text-anchor="start" x="2809.05" y="-746.32" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">6</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="2827.94,-733.12 2827.94,-765.92 2917.22,-765.92 2917.22,-733.12 2827.94,-733.12"/>
<text xml:space="preserve" text-anchor="start" x="2830.94" y="-743.92" font-family="Arial" font-size="14.00" fill="#c9c9c9">PlanProposal</text>
</g>
<!-- authority&#45;&gt;sqlexecutor -->
<g id="edge8" class="edge">
<title>authority&#45;&gt;sqlexecutor</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M2664.15,-448.91C2684.34,-440.66 2704.74,-432.64 2724.41,-425.4 2843.24,-381.66 2979.72,-339.82 3085.02,-309.3"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="3085.73,-311.82 3092.21,-307.22 3084.27,-306.78 3085.73,-311.82"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="2732.08,-428.4 2732.08,-468 2756.08,-468 2756.08,-428.4 2732.08,-428.4"/>
<text xml:space="preserve" text-anchor="start" x="2740.18" y="-445" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">7</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="2759.08,-428.4 2759.08,-468 2986.09,-468 2986.09,-428.4 2759.08,-428.4"/>
<text xml:space="preserve" text-anchor="start" x="2762.08" y="-451" font-family="Arial" font-size="14.00" fill="#c9c9c9">execute permitted fields when route</text>
<text xml:space="preserve" text-anchor="start" x="2837.56" y="-434.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">needs SQL</text>
</g>
<!-- authority&#45;&gt;executeapi -->
<g id="edge10" class="edge">
<title>authority&#45;&gt;executeapi</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M2664.24,-508.18C2684.5,-506.62 2704.9,-505.3 2724.41,-504.4 2843.99,-498.88 2874.5,-494 2993.75,-504.4 3015.96,-506.34 3039.1,-509.17 3062.05,-512.5"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="3061.42,-515.06 3069.22,-513.56 3062.19,-509.86 3061.42,-515.06"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="2727.41,-507.4 2727.41,-547 2751.41,-547 2751.41,-507.4 2727.41,-507.4"/>
<text xml:space="preserve" text-anchor="start" x="2735.52" y="-524" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">9</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="2754.41,-507.4 2754.41,-547 2990.75,-547 2990.75,-507.4 2754.41,-507.4"/>
<text xml:space="preserve" text-anchor="start" x="2757.41" y="-530" font-family="Arial" font-size="14.00" fill="#c9c9c9">POST /internal/v1/runs/{id}/execute ·</text>
<text xml:space="preserve" text-anchor="start" x="2828.21" y="-513.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">approved plan</text>
</g>
<!-- planapi&#45;&gt;normalizer -->
<g id="edge5" class="edge">
<title>planapi&#45;&gt;normalizer</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M3465.9,-841C3586.9,-841 3738.42,-841 3853.6,-841"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="3853.4,-843.63 3860.9,-841 3853.4,-838.38 3853.4,-843.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="3559.83,-844 3559.83,-876.8 3583.83,-876.8 3583.83,-844 3559.83,-844"/>
<text xml:space="preserve" text-anchor="start" x="3567.94" y="-857.2" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">4</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="3586.83,-844 3586.83,-876.8 3750.79,-876.8 3750.79,-844 3586.83,-844"/>
<text xml:space="preserve" text-anchor="start" x="3589.83" y="-854.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">normalize questionFrame</text>
</g>
<!-- normalizer&#45;&gt;planner -->
<g id="edge6" class="edge">
<title>normalizer&#45;&gt;planner</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M4193.52,-841C4322.7,-841 4502.78,-841 4636.81,-841"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="4636.66,-843.63 4644.16,-841 4636.66,-838.38 4636.66,-843.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="4297.53,-844 4297.53,-876.8 4321.53,-876.8 4321.53,-844 4297.53,-844"/>
<text xml:space="preserve" text-anchor="start" x="4305.64" y="-857.2" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">5</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="4324.53,-844 4324.53,-876.8 4540.64,-876.8 4540.64,-844 4324.53,-844"/>
<text xml:space="preserve" text-anchor="start" x="4327.53" y="-854.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">select route · propose constraints</text>
</g>
<!-- sqlexecutor&#45;&gt;businessschema -->
<g id="edge9" class="edge">
<title>sqlexecutor&#45;&gt;businessschema</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M3424.94,-261C3551.09,-261 3724.98,-261 3853.58,-261"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="3853.4,-263.63 3860.9,-261 3853.4,-258.38 3853.4,-263.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="3529.09,-264 3529.09,-296.8 3553.09,-296.8 3553.09,-264 3529.09,-264"/>
<text xml:space="preserve" text-anchor="start" x="3537.2" y="-277.2" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">8</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="3556.09,-264 3556.09,-296.8 3781.53,-296.8 3781.53,-264 3556.09,-264"/>
<text xml:space="preserve" text-anchor="start" x="3559.09" y="-274.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">parameterized SQL · business role</text>
</g>
<!-- executeapi&#45;&gt;planvalidator -->
<g id="edge11" class="edge">
<title>executeapi&#45;&gt;planvalidator</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M3447.51,-551C3564.78,-551 3715.75,-551 3834.29,-551"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="3834.04,-553.63 3841.54,-551 3834.04,-548.38 3834.04,-553.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="3559.15,-554 3559.15,-593.6 3590.72,-593.6 3590.72,-554 3559.15,-554"/>
<text xml:space="preserve" text-anchor="start" x="3567.15" y="-570.6" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">10</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="3593.72,-554 3593.72,-593.6 3751.47,-593.6 3751.47,-554 3593.72,-554"/>
<text xml:space="preserve" text-anchor="start" x="3618.52" y="-576.6" font-family="Arial" font-size="14.00" fill="#c9c9c9">verify planHash ·</text>
<text xml:space="preserve" text-anchor="start" x="3596.72" y="-559.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">corpus/config/revocation</text>
</g>
<!-- planvalidator&#45;&gt;lexical -->
<g id="edge12" class="edge">
<title>planvalidator&#45;&gt;lexical</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M4212.58,-551C4343.16,-551 4517.71,-551 4646.26,-551"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="4646.07,-553.63 4653.57,-551 4646.07,-548.38 4646.07,-553.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="4294.91,-554 4294.91,-586.8 4326.48,-586.8 4326.48,-554 4294.91,-554"/>
<text xml:space="preserve" text-anchor="start" x="4302.91" y="-567.2" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">11</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="4329.48,-554 4329.48,-586.8 4543.26,-586.8 4543.26,-554 4329.48,-554"/>
<text xml:space="preserve" text-anchor="start" x="4332.48" y="-564.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">BM25 when route includes lexical</text>
</g>
<!-- planvalidator&#45;&gt;dense -->
<g id="edge13" class="edge">
<title>planvalidator&#45;&gt;dense</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M4212.58,-483.92C4333.06,-439.74 4490.99,-381.81 4615.66,-336.09"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="4616.36,-338.63 4622.5,-333.58 4614.55,-333.7 4616.36,-338.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="4275.84,-460.2 4275.84,-493 4307.41,-493 4307.41,-460.2 4275.84,-460.2"/>
<text xml:space="preserve" text-anchor="start" x="4283.84" y="-473.4" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">12</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="4310.41,-460.2 4310.41,-493 4562.34,-493 4562.34,-460.2 4310.41,-460.2"/>
<text xml:space="preserve" text-anchor="start" x="4313.41" y="-471" font-family="Arial" font-size="14.00" fill="#c9c9c9">384D vector when route includes dense</text>
</g>
<!-- lexical&#45;&gt;fusion -->
<g id="edge14" class="edge">
<title>lexical&#45;&gt;fusion</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M4986.09,-486.33C5088.13,-446.01 5219.57,-394.08 5324.72,-352.53"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="5325.67,-354.98 5331.68,-349.79 5323.74,-350.1 5325.67,-354.98"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="5098.36,-451.12 5098.36,-483.92 5129.93,-483.92 5129.93,-451.12 5098.36,-451.12"/>
<text xml:space="preserve" text-anchor="start" x="5106.36" y="-464.32" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">13</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="5132.93,-451.12 5132.93,-483.92 5253.34,-483.92 5253.34,-451.12 5132.93,-451.12"/>
<text xml:space="preserve" text-anchor="start" x="5135.93" y="-461.92" font-family="Arial" font-size="14.00" fill="#c9c9c9">ranked candidates</text>
</g>
<!-- dense&#45;&gt;fusion -->
<g id="edge15" class="edge">
<title>dense&#45;&gt;fusion</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M5017.32,-266.7C5113.81,-269.53 5229.58,-272.92 5324.19,-275.69"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="5323.85,-278.3 5331.42,-275.9 5324,-273.05 5323.85,-278.3"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="5098.36,-276.96 5098.36,-309.76 5129.93,-309.76 5129.93,-276.96 5098.36,-276.96"/>
<text xml:space="preserve" text-anchor="start" x="5106.36" y="-290.16" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">14</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="5132.93,-276.96 5132.93,-309.76 5253.34,-309.76 5253.34,-276.96 5132.93,-276.96"/>
<text xml:space="preserve" text-anchor="start" x="5135.93" y="-287.76" font-family="Arial" font-size="14.00" fill="#c9c9c9">ranked candidates</text>
</g>
<!-- fusion&#45;&gt;evidence -->
<g id="edge16" class="edge">
<title>fusion&#45;&gt;evidence</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M5679.14,-281C5798.84,-281 5958.11,-281 6078.44,-281"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="6078.33,-283.63 6085.83,-281 6078.33,-278.38 6078.33,-283.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="5742.33,-284 5742.33,-316.8 5773.9,-316.8 5773.9,-284 5742.33,-284"/>
<text xml:space="preserve" text-anchor="start" x="5750.33" y="-297.2" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">15</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="5776.9,-284 5776.9,-316.8 6025.66,-316.8 6025.66,-284 5776.9,-284"/>
<text xml:space="preserve" text-anchor="start" x="5779.9" y="-294.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">RRF only when both lists exist · rerank</text>
</g>
<!-- evidence&#45;&gt;prompt -->
<g id="edge17" class="edge">
<title>evidence&#45;&gt;prompt</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M6418.58,-281C6519.28,-281 6648.46,-281 6752.47,-281"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="6752.24,-283.63 6759.74,-281 6752.24,-278.38 6752.24,-283.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="6481.71,-284 6481.71,-316.8 6513.28,-316.8 6513.28,-284 6481.71,-284"/>
<text xml:space="preserve" text-anchor="start" x="6489.71" y="-297.2" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">16</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="6516.28,-284 6516.28,-316.8 6699.71,-316.8 6699.71,-284 6516.28,-284"/>
<text xml:space="preserve" text-anchor="start" x="6519.28" y="-294.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">EvidenceSet · source spans</text>
</g>
<!-- prompt&#45;&gt;generator -->
<g id="edge18" class="edge">
<title>prompt&#45;&gt;generator</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M7109.96,-278.15C7190.88,-276.81 7287.1,-275.22 7368.23,-273.88"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="7368.07,-276.51 7375.52,-273.76 7367.98,-271.26 7368.07,-276.51"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="7172.99,-279.9 7172.99,-312.7 7204.56,-312.7 7204.56,-279.9 7172.99,-279.9"/>
<text xml:space="preserve" text-anchor="start" x="7180.99" y="-293.1" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">17</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="7207.56,-279.9 7207.56,-312.7 7315.52,-312.7 7315.52,-279.9 7207.56,-279.9"/>
<text xml:space="preserve" text-anchor="start" x="7210.56" y="-290.7" font-family="Arial" font-size="14.00" fill="#c9c9c9">bounded prompt</text>
</g>
<!-- generator&#45;&gt;gemini -->
<g id="edge19" class="edge">
<title>generator&#45;&gt;gemini</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M7708.17,-230.49C7812.16,-204.75 7947.92,-171.14 8060.58,-143.25"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="8061.12,-145.82 8067.77,-141.47 8059.86,-140.72 8061.12,-145.82"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="7771.57,-215.45 7771.57,-248.25 7803.14,-248.25 7803.14,-215.45 7771.57,-215.45"/>
<text xml:space="preserve" text-anchor="start" x="7779.57" y="-228.65" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">18</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="7806.14,-215.45 7806.14,-248.25 8007.5,-248.25 8007.5,-215.45 7806.14,-215.45"/>
<text xml:space="preserve" text-anchor="start" x="7809.14" y="-226.25" font-family="Arial" font-size="14.00" fill="#c9c9c9">grounded structured generation</text>
</g>
<!-- finalvalidator&#45;&gt;proposalvalidator -->
<g id="edge21" class="edge">
<title>finalvalidator&#45;&gt;proposalvalidator</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1113.7,-335.93C1240.36,-320.58 1411.84,-299.8 1542.08,-284.01"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1113.64,-333.29 1106.52,-336.8 1114.28,-338.51 1113.64,-333.29"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1267.5,-326.21 1267.5,-359.01 1299.07,-359.01 1299.07,-326.21 1267.5,-326.21"/>
<text xml:space="preserve" text-anchor="start" x="1275.5" y="-339.41" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">20</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1302.07,-326.21 1302.07,-359.01 1421.7,-359.01 1421.7,-326.21 1302.07,-326.21"/>
<text xml:space="preserve" text-anchor="start" x="1305.07" y="-337.01" font-family="Arial" font-size="14.00" fill="#c9c9c9">ValidatedProposal</text>
</g>
<!-- finalvalidator&#45;&gt;persistence -->
<g id="edge22" class="edge">
<title>finalvalidator&#45;&gt;persistence</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1103.51,-397.08C1228.7,-427.74 1401.83,-470.14 1534.68,-502.68"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1533.73,-505.15 1541.63,-504.38 1534.97,-500.05 1533.73,-505.15"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1229.79,-491.25 1229.79,-524.05 1261.36,-524.05 1261.36,-491.25 1229.79,-491.25"/>
<text xml:space="preserve" text-anchor="start" x="1237.79" y="-504.45" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">21</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1264.36,-491.25 1264.36,-524.05 1459.4,-524.05 1459.4,-491.25 1264.36,-491.25"/>
<text xml:space="preserve" text-anchor="start" x="1267.36" y="-502.05" font-family="Arial" font-size="14.00" fill="#c9c9c9">rights · claim · filters re&#45;check</text>
</g>
<!-- proposalvalidator&#45;&gt;gemini -->
<g id="edge20" class="edge">
<title>proposalvalidator&#45;&gt;gemini</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1906.57,-166.54C2056.1,-93.59 2280.59,-5 2489.04,-5 2489.04,-5 2489.04,-5 7544.55,-5 7723.13,-5 7924.61,-30.33 8070.77,-53.34"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1905.57,-164.11 1899.99,-169.77 1907.88,-168.82 1905.57,-164.11"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="5080.47,-8 5080.47,-40.8 5112.04,-40.8 5112.04,-8 5080.47,-8"/>
<text xml:space="preserve" text-anchor="start" x="5088.47" y="-21.2" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">19</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="5115.04,-8 5115.04,-40.8 5271.23,-40.8 5271.23,-8 5115.04,-8"/>
<text xml:space="preserve" text-anchor="start" x="5118.04" y="-18.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">claim/evidence proposal</text>
</g>
</g>
</svg>
`;case`offline-corpus-quality`:return`<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
 "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<!-- Generated by graphviz version 16.1.0 (0)
 -->
<!-- Pages: 1 -->
<svg width="2944pt" height="933pt"
 viewBox="0.00 0.00 2944.00 933.00" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
<g id="graph0" class="graph" transform="scale(1 1) rotate(0) translate(15.05 918.05)">
<g id="clust1" class="cluster">
<title>cluster_onmaru</title>
<polygon fill="#194b9e" stroke="#1b3d88" points="830.66,-8 830.66,-895 2905.85,-895 2905.85,-8 830.66,-8"/>
<text xml:space="preserve" text-anchor="start" x="838.66" y="-882.1" font-family="Arial" font-weight="bold" font-size="11.00" fill="#bfdbfe" fill-opacity="0.701961">ONMARU</text>
</g>
<!-- spring -->
<g id="node1" class="node">
<title>spring</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1327.75,-228 870.66,-228 870.66,-48 1327.75,-48 1327.75,-228"/>
<text xml:space="preserve" text-anchor="start" x="1019.17" y="-150.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Spring API Server</text>
<text xml:space="preserve" text-anchor="start" x="910.66" y="-129.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">회원 인증·대화·쿼리 권한·정형 SQL·최종 검증·영속화·SSE를 소유한다.</text>
<text xml:space="preserve" text-anchor="start" x="1012.09" y="-108.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Spring Boot · 독립 프로세스</text>
</g>
<!-- businessschema -->
<g id="node2" class="node">
<title>businessschema</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1264.23,-518 934.18,-518 934.18,-338 1264.23,-338 1264.23,-518"/>
<text xml:space="preserve" text-anchor="start" x="1019.17" y="-440.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Business Schema</text>
<text xml:space="preserve" text-anchor="start" x="994.08" y="-419.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">회원·대화·장소·권리의 canonical data.</text>
<text xml:space="preserve" text-anchor="start" x="1052.93" y="-398.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">Spring&#45;owned</text>
</g>
<!-- corpusworker -->
<g id="node3" class="node">
<title>corpusworker</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="2106.86,-251 1714.76,-251 1714.76,-71 2106.86,-71 2106.86,-251"/>
<text xml:space="preserve" text-anchor="start" x="1843.58" y="-173.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Corpus Worker</text>
<text xml:space="preserve" text-anchor="start" x="1754.76" y="-152.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">공개 projection을 파싱·청킹·enrichment·임베딩·색인한다.</text>
<text xml:space="preserve" text-anchor="start" x="1852.87" y="-131.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">offline / serialized</text>
</g>
<!-- aischema -->
<g id="node4" class="node">
<title>aischema</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="2865.85,-251 2514.88,-251 2514.88,-71 2865.85,-71 2865.85,-251"/>
<text xml:space="preserve" text-anchor="start" x="2606.44" y="-173.8" font-family="Arial" font-size="20.00" fill="#eff6ff">AI Corpus Schema</text>
<text xml:space="preserve" text-anchor="start" x="2554.88" y="-152.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">source/revision/chunk/vector/BM25 metadata와</text>
<text xml:space="preserve" text-anchor="start" x="2620.33" y="-131.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">AI least&#45;privilege role</text>
</g>
<!-- admin -->
<g id="node5" class="node">
<title>admin</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="473.55,-808 0,-808 0,-628 473.55,-628 473.55,-808"/>
<text xml:space="preserve" text-anchor="start" x="211.77" y="-730" font-family="Arial" font-size="20.00" fill="#eff6ff">운영자</text>
<text xml:space="preserve" text-anchor="start" x="20.06" y="-707" font-family="Arial" font-size="15.00" fill="#bfdbfe">Grafana 검토 큐에서 품질 저하 사례를 선택해 격리 실험을 시작하고 승격을</text>
<text xml:space="preserve" text-anchor="start" x="209.69" y="-689" font-family="Arial" font-size="15.00" fill="#bfdbfe">승인한다.</text>
</g>
<!-- qualityharness -->
<g id="node6" class="node">
<title>qualityharness</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="1315.84,-808 882.58,-808 882.58,-628 1315.84,-628 1315.84,-808"/>
<text xml:space="preserve" text-anchor="start" x="1028.07" y="-730.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Quality Harness</text>
<text xml:space="preserve" text-anchor="start" x="922.58" y="-709.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">trace·gold 평가에서 실패를 분류하고 선택된 격리 실험 결과를 만든다.</text>
<text xml:space="preserve" text-anchor="start" x="988.72" y="-688.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">asynchronous / human controlled</text>
</g>
<!-- evalschema -->
<g id="node7" class="node">
<title>evalschema</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="2092.81,-544 1728.81,-544 1728.81,-364 2092.81,-364 2092.81,-544"/>
<text xml:space="preserve" text-anchor="start" x="1825.22" y="-466.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Evaluation Artifacts</text>
<text xml:space="preserve" text-anchor="start" x="1768.81" y="-445.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">dataset hash·expected evidence·version·review</text>
<text xml:space="preserve" text-anchor="start" x="1852.45" y="-424.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">access&#45;controlled</text>
</g>
<!-- planner -->
<g id="node8" class="node">
<title>planner</title>
<polygon fill="#3b82f6" stroke="#2563eb" stroke-width="0" points="2085.05,-834 1736.58,-834 1736.58,-654 2085.05,-654 2085.05,-834"/>
<text xml:space="preserve" text-anchor="start" x="1804.09" y="-756.8" font-family="Arial" font-size="20.00" fill="#eff6ff">Query Planner &amp; Router</text>
<text xml:space="preserve" text-anchor="start" x="1816.54" y="-735.8" font-family="Arial" font-size="13.00" fill="#bfdbfe">결정적 route와 조회 제약을 제안한다.</text>
<text xml:space="preserve" text-anchor="start" x="1776.58" y="-714.2" font-family="Arial" font-size="15.00" fill="#bfdbfe">SQL / lexical / dense / hybrid / combined</text>
</g>
<!-- spring&#45;&gt;corpusworker -->
<g id="edge1" class="edge">
<title>spring&#45;&gt;corpusworker</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1327.64,-132.12C1427.98,-130.88 1547.3,-131.23 1654.76,-136.4 1670.95,-137.18 1687.7,-138.23 1704.52,-139.47"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1704.3,-142.09 1711.98,-140.04 1704.7,-136.85 1704.3,-142.09"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1416.04,-139.4 1416.04,-179 1440.04,-179 1440.04,-139.4 1416.04,-139.4"/>
<text xml:space="preserve" text-anchor="start" x="1424.15" y="-156" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">0</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1443.04,-139.4 1443.04,-179 1626.47,-179 1626.47,-139.4 1443.04,-139.4"/>
<text xml:space="preserve" text-anchor="start" x="1446.04" y="-162" font-family="Arial" font-size="14.00" fill="#c9c9c9">versioned public projection ·</text>
<text xml:space="preserve" text-anchor="start" x="1483.4" y="-145.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">rights/revocation</text>
</g>
<!-- businessschema&#45;&gt;corpusworker -->
<g id="edge3" class="edge">
<title>businessschema&#45;&gt;corpusworker</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1264.01,-373.28C1304.44,-359.81 1347.66,-345.45 1387.75,-332.2 1492.27,-297.65 1608.66,-259.46 1704.97,-227.93"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1705.63,-230.47 1711.94,-225.64 1704,-225.48 1705.63,-230.47"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1419.94,-335.2 1419.94,-368 1443.94,-368 1443.94,-335.2 1419.94,-335.2"/>
<text xml:space="preserve" text-anchor="start" x="1428.05" y="-348.4" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">2</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1446.94,-335.2 1446.94,-368 1622.57,-368 1622.57,-335.2 1446.94,-335.2"/>
<text xml:space="preserve" text-anchor="start" x="1449.94" y="-346" font-family="Arial" font-size="14.00" fill="#c9c9c9">public&#45;only source manifest</text>
</g>
<!-- corpusworker&#45;&gt;aischema -->
<g id="edge2" class="edge">
<title>corpusworker&#45;&gt;aischema</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M2106.77,-161C2228.72,-161 2384.86,-161 2504.8,-161"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="2504.67,-163.63 2512.17,-161 2504.67,-158.38 2504.67,-163.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="2169.86,-164 2169.86,-203.6 2193.86,-203.6 2193.86,-164 2169.86,-164"/>
<text xml:space="preserve" text-anchor="start" x="2177.97" y="-180.6" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">1</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="2196.86,-164 2196.86,-203.6 2451.88,-203.6 2451.88,-164 2196.86,-164"/>
<text xml:space="preserve" text-anchor="start" x="2199.86" y="-186.6" font-family="Arial" font-size="14.00" fill="#c9c9c9">parse · chunk · enrich · embed · index</text>
<text xml:space="preserve" text-anchor="start" x="2274.57" y="-169.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">inactive revision</text>
</g>
<!-- admin&#45;&gt;qualityharness -->
<g id="edge6" class="edge">
<title>admin&#45;&gt;qualityharness</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M473.46,-718C597.83,-718 749.68,-718 872.53,-718"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="872.29,-720.63 879.79,-718 872.29,-715.38 872.29,-720.63"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="536.55,-721 536.55,-753.8 560.55,-753.8 560.55,-721 536.55,-721"/>
<text xml:space="preserve" text-anchor="start" x="544.66" y="-734.2" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">5</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="563.55,-721 563.55,-753.8 807.66,-753.8 807.66,-721 563.55,-721"/>
<text xml:space="preserve" text-anchor="start" x="566.55" y="-731.8" font-family="Arial" font-size="14.00" fill="#c9c9c9">select case · start isolated experiment</text>
</g>
<!-- qualityharness&#45;&gt;evalschema -->
<g id="edge4" class="edge">
<title>qualityharness&#45;&gt;evalschema</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1265.75,-628.05C1288.2,-611.58 1309.69,-593.14 1327.75,-573 1367.98,-528.13 1336.57,-483.22 1387.75,-451.4 1485.06,-390.9 1613.58,-390.79 1718.75,-406.18"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1718.05,-408.73 1725.86,-407.26 1718.84,-403.54 1718.05,-408.73"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1390.75,-454.4 1390.75,-494 1414.75,-494 1414.75,-454.4 1390.75,-454.4"/>
<text xml:space="preserve" text-anchor="start" x="1398.86" y="-471" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">3</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1417.75,-454.4 1417.75,-494 1651.76,-494 1651.76,-454.4 1417.75,-454.4"/>
<text xml:space="preserve" text-anchor="start" x="1420.75" y="-477" font-family="Arial" font-size="14.00" fill="#c9c9c9">persist run observations · evaluation</text>
<text xml:space="preserve" text-anchor="start" x="1510.25" y="-460.2" font-family="Arial" font-size="14.00" fill="#c9c9c9">artifacts</text>
</g>
<!-- qualityharness&#45;&gt;evalschema -->
<g id="edge5" class="edge">
<title>qualityharness&#45;&gt;evalschema</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1325.46,-644.55C1452.71,-603.05 1609.66,-551.87 1728.85,-513.01"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1324.77,-642.01 1318.45,-646.83 1326.39,-647 1324.77,-642.01"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1404.36,-620.41 1404.36,-653.21 1428.36,-653.21 1428.36,-620.41 1404.36,-620.41"/>
<text xml:space="preserve" text-anchor="start" x="1412.46" y="-633.61" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">4</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1431.36,-620.41 1431.36,-653.21 1638.16,-653.21 1638.16,-620.41 1431.36,-620.41"/>
<text xml:space="preserve" text-anchor="start" x="1434.36" y="-631.21" font-family="Arial" font-size="14.00" fill="#c9c9c9">gold replay · expected evidence</text>
</g>
<!-- qualityharness&#45;&gt;planner -->
<g id="edge7" class="edge">
<title>qualityharness&#45;&gt;planner</title>
<path fill="none" stroke="#8d8d8d" stroke-width="2" stroke-dasharray="5,2" d="M1315.57,-724.92C1443.72,-729.03 1604.57,-734.2 1726.59,-738.12"/>
<polygon fill="#8d8d8d" stroke="#8d8d8d" stroke-width="2" points="1726.18,-740.73 1733.76,-738.35 1726.35,-735.48 1726.18,-740.73"/>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1399.69,-738.59 1399.69,-778.19 1423.69,-778.19 1423.69,-738.59 1399.69,-738.59"/>
<text xml:space="preserve" text-anchor="start" x="1407.8" y="-755.19" font-family="Arial" font-weight="bold" font-size="14.00" fill="#c9c9c9">6</text>
<polygon fill="#18191b" fill-opacity="0.627451" stroke="none" points="1426.69,-738.59 1426.69,-778.19 1642.82,-778.19 1642.82,-738.59 1426.69,-738.59"/>
<text xml:space="preserve" text-anchor="start" x="1429.69" y="-761.19" font-family="Arial" font-size="14.00" fill="#c9c9c9">candidate config only after human</text>
<text xml:space="preserve" text-anchor="start" x="1507.9" y="-744.39" font-family="Arial" font-size="14.00" fill="#c9c9c9">approval</text>
</g>
</g>
</svg>
`;default:throw Error(`Unknown viewId: `+e)}};export{e as dotSource,t as svgSource};