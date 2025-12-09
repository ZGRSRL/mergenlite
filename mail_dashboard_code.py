
def render_mail_dashboard():
    """İletişim/Mail Dashboard Ekranı - 3 Panelli Tasarım"""
    st.markdown('<h1 class="main-header">📨 İletişim Merkezi</h1>', unsafe_allow_html=True)
    
    # 3-Panel Layout Container
    # Sol: Aktif Operasyonlar (%20)
    # Orta: Hedef Oteller (%30)
    # Sağ: Detay/Chat (%50)
    
    col_ops, col_hotels, col_chat = st.columns([2, 3, 5], gap="medium")
    
    db = get_db_session()
    if not db:
        st.error("Veritabanı bağlantısı yok.")
        return

    # Session State Yönetimi
    if 'mail_selected_opp_id' not in st.session_state:
        st.session_state.mail_selected_opp_id = None
    if 'mail_selected_hotel_id' not in st.session_state:
        st.session_state.mail_selected_hotel_id = None

    try:
        # --- SOL PANEL: Aktif Operasyonlar ---
        with col_ops:
            st.markdown("### 🏢 Aktif Operasyonlar", unsafe_allow_html=True)
            
            # Arama Kutusu
            search_query = st.text_input("Fırsat Ara...", key="mail_opp_search", placeholder="Fırsat başlığı veya ID...")
            
            # Aktif fırsatları çek
            ops_query = db.query(Opportunity).filter(Opportunity.status != 'archived')
            if search_query:
                ops_query = ops_query.filter(Opportunity.title.ilike(f"%{search_query}%"))
            
            opportunities = ops_query.order_by(Opportunity.updated_at.desc()).limit(20).all()
            
            st.markdown('<div style="height: 600px; overflow-y: auto; padding-right: 5px;">', unsafe_allow_html=True)
            
            for opp in opportunities:
                # Aktiflik durumu (CSS class)
                is_active = (st.session_state.mail_selected_opp_id == opp.id)
                card_style = "border: 1px solid var(--blue-500); background: rgba(59, 130, 246, 0.1);" if is_active else "border: 1px solid var(--border-800); background: rgba(15, 23, 42, 0.5);"
                
                # İstatistikler (Mock veya DB'den)
                # Gerçekte Hotel tablosundan sayılmalı ama performans için burada basit tutuyoruz veya join yapıyoruz
                hotel_count = db.query(Hotel).filter(Hotel.opportunity_id == opp.id).count()
                
                st.markdown(f"""
                <div class="modern-card" style="{card_style} padding: 12px; margin-bottom: 12px; cursor: pointer;">
                    <div style="font-size: 11px; color: var(--blue-400); margin-bottom: 4px;">{opp.opportunity_id}</div>
                    <div style="font-weight: 600; font-size: 13px; margin-bottom: 8px; line-height: 1.4;">{opp.title[:60]}...</div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="badge badge-info">{hotel_count} Otel</span>
                        <span style="font-size: 11px; color: var(--text-400);">{opp.updated_at.strftime('%d %b') if opp.updated_at else ''}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Görünmez buton
                if st.button(f"Seç {opp.id}", key=f"btn_opp_{opp.id}", use_container_width=True):
                    st.session_state.mail_selected_opp_id = opp.id
                    st.session_state.mail_selected_hotel_id = None # Reset hotel selection
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

        # --- ORTA PANEL: Hedef Oteller ---
        with col_hotels:
            st.markdown("### 🏨 Hedef Oteller", unsafe_allow_html=True)
            
            if st.session_state.mail_selected_opp_id:
                hotels = db.query(Hotel).filter(Hotel.opportunity_id == st.session_state.mail_selected_opp_id).all()
                
                if not hotels:
                    st.info("Bu fırsat için henüz otel bulunamadı.")
                
                st.markdown('<div style="height: 600px; overflow-y: auto; padding-right: 5px;">', unsafe_allow_html=True)
                
                for hotel in hotels:
                    is_active = (st.session_state.mail_selected_hotel_id == hotel.id)
                    hotel_style = "border-left: 3px solid var(--blue-500); background: rgba(59, 130, 246, 0.05);" if is_active else "border-left: 3px solid transparent;"
                    
                    status_colors = {
                        'queued': 'badge-warning',
                        'sent': 'badge-info', 
                        'replied': 'badge-success',
                        'negotiating': 'badge-purple',
                        'rejected': 'badge-danger'
                    }
                    badge_class = status_colors.get(hotel.status, 'badge-info')
                    
                    st.markdown(f"""
                    <div style="{hotel_style} padding: 12px; border-bottom: 1px solid var(--border-800); transition: background 0.2s;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span style="font-weight: 600; font-size: 14px;">{hotel.name}</span>
                            <span class="badge {badge_class}">{hotel.status or 'queued'}</span>
                        </div>
                        <div style="font-size: 12px; color: var(--text-400); margin-bottom: 4px;">{hotel.manager_name or 'Yetkili Yok'}</div>
                        <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--text-400);">
                            <span>{hotel.price_quote or '-'}</span>
                            <span>{hotel.last_contact_at.strftime('%H:%M') if hotel.last_contact_at else ''}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"Chat {hotel.id}", key=f"btn_hotel_{hotel.id}", use_container_width=True):
                        st.session_state.mail_selected_hotel_id = hotel.id
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("👈 Lütfen sol panelden bir operasyon seçin.")

        # --- SAĞ PANEL: Mesajlaşma / Chat ---
        with col_chat:
            if st.session_state.mail_selected_hotel_id:
                hotel = db.query(Hotel).filter(Hotel.id == st.session_state.mail_selected_hotel_id).first()
                if hotel:
                    # Header
                    st.markdown(f"""
                    <div style="background: rgba(15, 23, 42, 0.8); padding: 16px; border-radius: 8px; margin-bottom: 16px; border: 1px solid var(--border-800);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h3 style="margin: 0; font-size: 16px;">{hotel.name}</h3>
                                <div style="font-size: 12px; color: var(--text-400);">{hotel.manager_name} • ⭐ {hotel.rating or 4.5}</div>
                            </div>
                            <div style="display: flex; gap: 8px;">
                                <div class="badge badge-success">Online</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Chat History Area
                    messages = db.query(EmailLog).filter(EmailLog.hotel_id == hotel.id).order_by(EmailLog.created_at.asc()).all()
                    
                    chat_container = st.container()
                    with chat_container:
                        st.markdown('<div style="height: 450px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; padding: 10px;">', unsafe_allow_html=True)
                        
                        if not messages:
                            st.info("Henüz mesaj geçmişi yok.")
                        
                        for msg in messages:
                            align = "flex-end" if msg.direction == 'outbound' else "flex-start"
                            bg_color = "rgba(59, 130, 246, 0.2)" if msg.direction == 'outbound' else "rgba(31, 41, 55, 0.8)"
                            border_color = "var(--blue-500)" if msg.direction == 'outbound' else "var(--border-800)"
                            
                            st.markdown(f"""
                            <div style="display: flex; justify-content: {align}; width: 100%;">
                                <div style="background: {bg_color}; border: 1px solid {border_color}; padding: 10px 14px; border-radius: 12px; max-width: 80%; width: fit-content;">
                                    <div style="font-size: 13px;">{msg.raw_body}</div>
                                    <div style="font-size: 10px; color: var(--text-400); margin-top: 4px; text-align: right;">{msg.created_at.strftime('%H:%M')}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Input Area
                    st.markdown("---")
                    with st.form(key="chat_input_form", clear_on_submit=True):
                        col_in, col_btn = st.columns([5, 1])
                        with col_in:
                            user_msg = st.text_input("Mesajınız...", label_visibility="collapsed", placeholder="Mesaj yazın veya AI önerisi seçin...")
                        with col_btn:
                            submitted = st.form_submit_button("Gönder")
                        
                        if submitted and user_msg:
                            # Save message to DB
                            new_log = EmailLog(
                                hotel_id=hotel.id,
                                opportunity_id=hotel.opportunity_id,
                                direction='outbound',
                                raw_body=user_msg,
                                subject="Chat Message",
                                created_at=datetime.utcnow()
                            )
                            db.add(new_log)
                            # Update hotel last contact
                            hotel.last_contact_at = datetime.utcnow()
                            hotel.status = 'negotiating'
                            db.commit()
                            st.rerun()
            else:
                 st.markdown("""
                 <div style="height: 100%; display: flex; align-items: center; justify-content: center; color: var(--text-400); flex-direction: column;">
                    <div style="font-size: 48px; margin-bottom: 16px;">💬</div>
                    <div>Detayları görmek için bir otel seçin.</div>
                 </div>
                 """, unsafe_allow_html=True)

    except Exception as e:
        logger.error(f"Mail Dashboard Hatası: {e}", exc_info=True)
        st.error(f"Bir hata oluştu: {str(e)}")
    finally:
        db.close()
