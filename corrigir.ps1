# Encontrar e substituir a função download_xml_s2220
$content = Get-Content "main.py" -Raw

$oldFunctionPattern = '@app\.route\(\'/s2220/download_xml/<int:id>\'\)\s+@login_required\s+def download_xml_s2220\(id\):.*?(?=\n@app\.route\(\'/s2220/view_xml)'

$newFunction = @"
@app.route('/s2220/download_xml/<int:id>')
@login_required
def download_xml_s2220(id):
    try:
        evento = EventoS2220.query.get_or_404(id)
        funcionario = evento.funcionario
        empresa = funcionario.empresa
        xml_str = gerar_xml_s2220(evento, empresa, funcionario, ambiente='2')
        buffer = BytesIO(xml_str.encode('utf-8'))
        return send_file(buffer, as_attachment=True, download_name=f's2220_{evento.id}.xml', mimetype='application/xml')
    except Exception as e:
        flash(f'Erro ao gerar XML: {str(e)}', 'error')
        return redirect(url_for('list_s2220'))

"@

# Substituir
$content = $content -replace $oldFunctionPattern, $newFunction

# Salvar
$content | Set-Content "main.py" -NoNewline

Write-Host "Função corrigida com sucesso!" -ForegroundColor Green
