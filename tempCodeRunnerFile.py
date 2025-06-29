# Route to fetch product suggestions based on input
# @app.route('/get_product_suggestions', methods=['GET'])
# def get_product_suggestions():
#     term = request.args.get('term', '')
#     cursor.execute("SELECT product_id, product_type, selling_price FROM Product WHERE product_type LIKE %s", (f"%{term}%",))
#     products = cursor.fetchall()
#     suggestions = [{'id': p[0], 'type': p[1], 'price': p[2]} for p in products]
#     return jsonify(suggestions)