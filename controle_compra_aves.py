from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from models.carga import Carga, CustoAve
from extensions import db
from datetime import datetime

def controle_compra_aves():
    @login_required
    def view():
        if not current_user.tipo == 'fechamento':
            flash('Acesso não autorizado. Apenas usuários do tipo fechamento podem acessar esta página.', 'error')
            return redirect(url_for('index'))

        if request.method == 'POST':
            if 'exportar' in request.form:
                data_inicial = request.form.get('data_inicial')
                data_final = request.form.get('data_final')
                carga_id = request.form.get('carga_id')
                formato = request.form.get('formato')
                
                cargas = get_cargas(data_inicial, data_final, carga_id)
                
                if formato == 'pdf':
                    return export_to_pdf(cargas)
                elif formato == 'excel':
                    return export_to_excel(cargas)
            
            elif 'salvar' in request.form:
                carga_id = request.form.get('carga_id')
                custo_carregamento = float(request.form.get('custo_carregamento', 0))
                comissao = float(request.form.get('comissao', 0))
                
                custo_ave = CustoAve.query.filter_by(carga_id=carga_id).first()
                if not custo_ave:
                    custo_ave = CustoAve(carga_id=carga_id)
                    db.session.add(custo_ave)
                
                custo_ave.custo_carregamento = custo_carregamento
                custo_ave.comissao = comissao
                custo_ave.atualizar_custo_total()
                
                try:
                    db.session.commit()
                    flash('Custos atualizados com sucesso!', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Erro ao atualizar custos: {str(e)}', 'error')
                    
                return redirect(url_for('controle_compra_aves'))
            
        data_inicial = request.args.get('data_inicial')
        data_final = request.args.get('data_final')
        carga_id = request.args.get('carga_id')
        
        cargas = get_cargas(data_inicial, data_final, carga_id)
        return render_template('controle_compra_aves.html', cargas=cargas)
    
    return view()
