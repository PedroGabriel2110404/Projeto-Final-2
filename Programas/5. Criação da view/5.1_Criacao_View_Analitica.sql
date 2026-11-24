CREATE OR REPLACE VIEW workspace.pf1.vw_analise_clubes_2020_2025 AS
SELECT
    CAST(re.id_clube AS BIGINT) AS id_clube,
    c.nome_clube,
    CAST(re.ano AS BIGINT) AS ano,

    -- Desempenho esportivo
    re.posicao_final,
    re.pontos,
    re.fase_copa_brasil,
    re.fase_libertadores,

    -- Ponte entre clube esportivo e cadastro financeiro
    cf.id_financeiro,

    -- Receitas e dívidas (BRL, milhões)
    df.receita_total_milhoes_brl,
    df.divida_reportada_milhoes_brl,

    -- Transferências (BRL, milhões)
    cv.compras_milhoes_brl,
    cv.vendas_milhoes_brl,

    -- Gastos de pessoal (BRL, milhões)
    gp.gastos_pessoal_milhoes_brl,

    -- Elenco: idade média e valor de mercado (EUR, milhões)
    e.idade_media_elenco,
    e.valor_elenco_milhoes_eur,

    -- Estrutura societária
    s.virou_saf,
    s.tipo_controle,
    s.data_entrada_saf,
    s.data_troca_controle

FROM workspace.pf1.resultados_esportivos re
LEFT JOIN workspace.pf1.clubes c
    ON CAST(c.id_clube AS BIGINT) = CAST(re.id_clube AS BIGINT)
LEFT JOIN workspace.pf1.clube_financeiro cf
    ON CAST(cf.id_clube AS BIGINT) = CAST(re.id_clube AS BIGINT)
   AND CAST(cf.ano AS BIGINT) = CAST(re.ano AS BIGINT)
LEFT JOIN workspace.pf1.dados_financeiros df
    ON CAST(df.id_financeiro AS BIGINT) = CAST(cf.id_financeiro AS BIGINT)
LEFT JOIN workspace.pf1.compras_e_vendas cv
    ON CAST(cv.id_financeiro AS BIGINT) = CAST(cf.id_financeiro AS BIGINT)
LEFT JOIN workspace.pf1.gastos_pessoal gp
    ON CAST(gp.id_financeiro AS BIGINT) = CAST(cf.id_financeiro AS BIGINT)
LEFT JOIN workspace.pf1.elencos e
    ON CAST(e.id_clube AS BIGINT) = CAST(re.id_clube AS BIGINT)
   AND CAST(e.ano AS BIGINT) = CAST(re.ano AS BIGINT)
LEFT JOIN workspace.pf1.saf s
    ON CAST(s.id_clube AS BIGINT) = CAST(re.id_clube AS BIGINT)
   AND CAST(s.ano AS BIGINT) = CAST(re.ano AS BIGINT);
