from flask import request, jsonify

from auth.controllers import get_current_user
from products.models import Product
from app import db
from closets.models import Closet
import uuid

def list_all_products_controller():
    return jsonify([product.toDict() for product in Product.query.all()])

def create_product_controller():
    request_form = request.json
    content_type = request.headers.get('Content-Type')
    dev = False
    if dev:
        print(request_form.keys())
        return jsonify({'message': 'ok', 'data': request_form})
    else:
        price_data = request_form.get("price", {})
        # Extract the actual price values from the nested structure
        default_price = price_data.get("default", {}).get("default", 0) if isinstance(price_data.get("default"), dict) else price_data.get("default", 0)
        original_price = price_data.get("original", {}).get("default") if isinstance(price_data.get("original"), dict) else price_data.get("original")
        
        # Default price meta if not provided
        default_price_meta = {
            "CURRENCY_CODE": "INR",
            "CURRENCY_LOGO": "Rs."
        }
        price_meta = price_data.get("meta", {}).get("meta", default_price_meta) if isinstance(price_data.get("meta"), dict) else price_data.get("meta", default_price_meta)
        
        price = {
            "default": default_price,
            "original": original_price,
            "meta": price_meta
        }
        label = request_form.get("label")
        description = request_form.get("description")
        meta = request_form.get("meta")
        match content_type:
            case 'application/json':
                images = request_form.get("images")
            case 'multipart/form-data':
                return jsonify({'message': 'Not Implemented'})
            case _:
                images = []
        new_product = Product(
            label=label,
            description=description,
            images=images,
            price=price,
            meta=meta,
            vendor_id=request_form.get("vendor_id"),
        )
        db.session.add(new_product)
        db.session.commit()

        response = Product.query.get(new_product.id).toDict()
        return jsonify(response)

def retrieve_product_controller(product_id):
    product = Product.query.get(product_id).toDict()
    return jsonify(product)

def external_retrieve_products_controller():
    user, status = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    print(f"Fetching for user: {user.id}")
    current_user_preferred_brand_ids = user.meta.get("PREFERRED_BRANDS", [])
    closet = Closet.query.get(user.currentClosetId)
    if not closet:
        return jsonify({"error": "Closet not found"}), 404
    current_user_closet = closet.toDict()
    print(f"Current user closet: {current_user_closet}")
    positive_ids = current_user_closet.get("positiveIds", []) or []
    negative_ids = current_user_closet.get("negativeIds", []) or []
    if positive_ids is None:
        positive_ids = []
    if negative_ids is None:
        negative_ids = []
    print(f"Positive ids: {positive_ids}")
    print(f"Negative ids: {negative_ids}")
    products = Product.query.filter(
        Product.vendor_id.in_(current_user_preferred_brand_ids),
        Product.id.notin_(positive_ids),
        Product.id.notin_(negative_ids)
    ).all()
    print(f"Filtered products: {len(products)}")
    products_output = [product.toDict() for product in products]
    if len(products_output) == 0:
        # return random 50 from list all
        products_output = Product.query.limit(50).all()
        products_output = [product.toDict() for product in products_output]
        return jsonify(products_output), 200
    # tags = []
    # colors = []
    # for p in products_output:
    #     tags.extend(
    #         p["meta"]["tags"]
    #     )
    #     colors.extend(
    #         p["meta"]["colors"]
    #     )
    # return jsonify({
    #     "products": products_output,
    #     "tags": list(set(tags)),
    #     "colors": list(set(colors))
    # }), 200
    return jsonify(products_output), 200

def external_retrieve_products_controller_no_filter(filters, user, start_index=0):
    # start_index = user.meta.get("CURRENT_PAGE_INDEX", 0)
    # products = Product.query.limit(20).offset(start_index * 20).all()
    #
    # # Track visited products
    # visited_products = user.meta.get("CURRENT_VISIT_IDS", [])
    # for product in products:
    #     visited_products.append(product.id)
    # user.meta["CURRENT_VISIT_IDS"] = visited_products
    # user.meta["CURRENT_PAGE_INDEX"] = start_index + 1
    # db.session.commit()
    return jsonify([p.toDict() for p in Product.query.all()])


def update_product_controller(product_id):
    request_form = request.json
    product = Product.query.get(product_id)

    for key, value in request_form.items():
        setattr(product, key, value)
    db.session.commit()

    response = Product.query.get(product_id).toDict()
    return jsonify(response)

def delete_product_controller(product_id):
    product = Product.query.get(product_id)
    db.session.delete(product)
    db.session.commit()

    return 'Product with Id "{}" deleted successfully!'.format(product_id)

def update_closet_product_ids_controller():
    request_form = request.json
    user, status = get_current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    current_closet_id = user.currentClosetId
    current_closet = Closet.query.get(current_closet_id)
    product_id = uuid.UUID(request_form["productId"])

    if request_form.get("response") == 1:
        print("current_closet.positiveIds", current_closet.positiveIds)
        if current_closet.positiveIds is None:
            current_closet.positiveIds = [product_id]
        else:
            current_closet.positiveIds = current_closet.positiveIds + [product_id]  # New list assignment
        print("current_closet.positiveIds", current_closet.positiveIds)
    elif request_form.get("response") == -1:
        print("current_closet.negativeIds", current_closet.negativeIds)
        if current_closet.negativeIds is None:
            current_closet.negativeIds = [product_id]
        else:
            current_closet.negativeIds = current_closet.negativeIds + [product_id]  # New list assignment
        print("current_closet.negativeIds", current_closet.negativeIds)

    print("current_closet.positiveIds", current_closet.positiveIds)
    print("current_closet.negativeIds", current_closet.negativeIds)

    db.session.commit()
    return jsonify({"message": "Closet updated successfully"})